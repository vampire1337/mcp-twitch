#!/usr/bin/env python3
"""
MCP Twitch Server - ОБНОВЛЕНО с самыми современными возможностями FastMCP!
Использует МАКСИМУМ возможностей FastMCP из коробки по состоянию на 2025:
- from_openapi для автоматической генерации инструментов
- RouteMap для фильтрации эндпоинтов по тегам  
- Tool Transform для улучшения инструментов
- АКТУАЛЬНЫЕ зависимости из pyproject.toml
- CLI фильтрация по группам
- Экспериментальный новый OpenAPI парсер (если доступен)
"""

import os
import sys
import argparse
import asyncio
import httpx
from pathlib import Path
import json
from typing import Optional, List, Dict, Any

from fastmcp import FastMCP, Context
from fastmcp.server.openapi import RouteMap, MCPType
from fastmcp.tools import Tool
from fastmcp.tools.tool_transform import ArgTransform

# Попытка использовать экспериментальный новый OpenAPI парсер
try:
    from fastmcp.experimental.server.openapi import FastMCPOpenAPI
    USE_EXPERIMENTAL_PARSER = True
    print("🧪 Using experimental FastMCP OpenAPI parser")
except ImportError:
    USE_EXPERIMENTAL_PARSER = False
    print("📚 Using standard FastMCP OpenAPI parser")


class TwitchMCPServer:
    """MCP сервер для Twitch API с продвинутой фильтрацией и трансформацией"""
    
    def __init__(self, client_id: Optional[str] = None, access_token: Optional[str] = None):
        self.client_id = client_id or os.getenv('TWITCH_CLIENT_ID')
        self.access_token = access_token or os.getenv('TWITCH_ACCESS_TOKEN')
        
        if not self.client_id:
            raise ValueError("Twitch Client ID is required. Set TWITCH_CLIENT_ID environment variable or pass client_id parameter.")
        
        # Создаем HTTP клиент с правильными заголовками для Twitch API
        headers = {
            'Client-Id': self.client_id,
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        if self.access_token:
            headers['Authorization'] = f'Bearer {self.access_token}'
        
        self.http_client = httpx.AsyncClient(
            base_url='https://api.twitch.tv/helix',
            headers=headers,
            timeout=30.0
        )
        
        # Загружаем OpenAPI спецификацию
        self.openapi_spec = self._load_openapi_spec()
        
        # Создаем базовый FastMCP сервер
        self.mcp = None
        
    def _load_openapi_spec(self) -> Dict[str, Any]:
        """Загружает РЕАЛЬНУЮ OpenAPI спецификацию из JSON файла"""
        spec_path = Path(__file__).parent / 'openapi.json'
        
        if not spec_path.exists():
            raise FileNotFoundError(f"РЕАЛЬНЫЙ OpenAPI файл не найден: {spec_path}")
        
        print("🚀 Loading REAL Twitch OpenAPI from DmitryScaletta/twitch-api-swagger...")
        with open(spec_path, 'r', encoding='utf-8') as f:
            spec = json.load(f)
            
        # Исправляем известные ошибки валидации в реальном OpenAPI
        print("🔧 Fixing OpenAPI validation issues...")
        if 'components' in spec and 'schemas' in spec['components']:
            schemas = spec['components']['schemas']
            
            # Исправляем тип Bool -> boolean
            for schema_name, schema in schemas.items():
                self._fix_schema_types(schema)
                    
        print(f"✅ OpenAPI loaded and fixed: {len(spec.get('paths', {}))} paths, {len(spec.get('components', {}).get('schemas', {}))} schemas")
        return spec
    
    def _fix_schema_types(self, obj: Any) -> None:
        """Рекурсивно исправляет типы в OpenAPI схемах"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key == 'type' and value == 'Bool':
                    obj[key] = 'boolean'
                    print(f"  🔧 Fixed type: Bool -> boolean")
                elif isinstance(value, (dict, list)):
                    self._fix_schema_types(value)
        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, (dict, list)):
                    self._fix_schema_types(item)
    
    def _create_route_maps(self, include_tags: Optional[List[str]] = None, 
                          exclude_tags: Optional[List[str]] = None) -> List[RouteMap]:
        """
        Создает карты маршрутов для фильтрации эндпоинтов по тегам.
        Использует возможности FastMCP для группировки инструментов.
        """
        route_maps = []
        
        # Если указаны теги для исключения - исключаем их
        if exclude_tags:
            for tag in exclude_tags:
                route_maps.append(
                    RouteMap(
                        tags={tag},
                        mcp_type=MCPType.EXCLUDE,
                    )
                )
        
        # Если указаны теги для включения - включаем только их
        if include_tags:
            # Сначала исключаем все
            route_maps.append(
                RouteMap(
                    pattern=r".*",
                    mcp_type=MCPType.EXCLUDE,
                )
            )
            # Затем включаем только нужные теги
            for tag in include_tags:
                route_maps.append(
                    RouteMap(
                        tags={tag},
                        mcp_type=MCPType.TOOL,
                    )
                )
        
        # Специальные правила для разных типов эндпоинтов
        
        # GET эндпоинты для поиска и аналитики делаем ресурсами
        route_maps.extend([
            RouteMap(
                methods=["GET"],
                pattern=r"^/search/.*",
                mcp_type=MCPType.RESOURCE,
            ),
            RouteMap(
                methods=["GET"], 
                pattern=r"^/analytics/.*",
                mcp_type=MCPType.RESOURCE,
            ),
        ])
        
        # POST/PATCH/DELETE остаются инструментами (по умолчанию)
        return route_maps
    
    def _create_tool_transformations(self) -> Dict[str, Dict[str, Any]]:
        """
        Создает трансформации для улучшения инструментов.
        Использует Tool Transform возможности FastMCP.
        """
        transformations = {
            # Улучшаем инструмент получения информации о каналах
            "get_channel_info": {
                "name": "get_twitch_channel",
                "description": "Получить информацию о Twitch канале по ID стримера. Возвращает название канала, текущую игру, язык и другую информацию.",
                "meta": {
                    "category": "channels",
                    "difficulty": "easy",
                    "rate_limit": "low"
                },
                "arguments": {
                    "broadcaster_id": {
                        "name": "streamer_id", 
                        "description": "ID стримера на Twitch (можно получить через get_users)"
                    }
                }
            },
            
            # Улучшаем поиск пользователей
            "get_users": {
                "name": "find_twitch_users",
                "description": "Найти пользователей Twitch по их логину или ID. Можно искать несколько пользователей одновременно.",
                "meta": {
                    "category": "users",
                    "difficulty": "easy",
                    "examples": ["ninja", "pokimane", "shroud"]
                },
                "arguments": {
                    "login": {
                        "name": "usernames",
                        "description": "Список логинов пользователей Twitch (например: ['ninja', 'pokimane'])"
                    },
                    "id": {
                        "name": "user_ids", 
                        "description": "Список ID пользователей Twitch"
                    }
                }
            },
            
            # Улучшаем получение стримов
            "get_streams": {
                "name": "get_live_streams",
                "description": "Получить информацию о текущих живых стримах. Можно фильтровать по пользователям, играм или языку.",
                "meta": {
                    "category": "streams",
                    "difficulty": "easy",
                    "data_freshness": "real-time"
                },
                "arguments": {
                    "user_login": {
                        "name": "streamers",
                        "description": "Список логинов стримеров для проверки"
                    },
                    "game_id": {
                        "name": "game_ids",
                        "description": "ID игр для фильтрации стримов"
                    },
                    "language": {
                        "name": "languages",
                        "description": "Языки стримов (например: ['en', 'ru', 'es'])"
                    }
                }
            },
            
            # Улучшаем поиск каналов
            "search_channels": {
                "name": "search_twitch_channels",
                "description": "Поиск каналов Twitch по названию или описанию. Можно искать только среди активных стримеров.",
                "meta": {
                    "category": "search",
                    "difficulty": "easy",
                    "use_cases": ["discovery", "research"]
                },
                "arguments": {
                    "query": {
                        "description": "Поисковый запрос (название канала или ключевые слова из описания)"
                    },
                    "live_only": {
                        "name": "only_live",
                        "description": "Искать только среди стримеров, которые сейчас в эфире"
                    }
                }
            },
            
            # Специальная трансформация для модерации с скрытыми параметрами
            "ban_user": {
                "name": "moderate_ban_user",
                "description": "Забанить пользователя в чате канала. Требует права модератора.",
                "meta": {
                    "category": "moderation",
                    "difficulty": "advanced",
                    "requires_auth": "moderator",
                    "destructive": True
                },
                "arguments": {
                    "broadcaster_id": {
                        "name": "channel_id",
                        "description": "ID канала где нужно забанить пользователя"
                    },
                    "moderator_id": {
                        "hide": True,
                        "default_factory": lambda: "auto"  # Будет определяться из токена
                    }
                }
            }
        }
        
        return transformations
    
    async def create_server(self, include_tags: Optional[List[str]] = None, 
                           exclude_tags: Optional[List[str]] = None,
                           enable_transformations: bool = True) -> FastMCP:
        """
        Создает FastMCP сервер с полной конфигурацией.
        Максимально использует возможности FastMCP из коробки.
        """
        
        # Создаем карты маршрутов для фильтрации
        route_maps = self._create_route_maps(include_tags, exclude_tags)
        
        # Создаем сервер из OpenAPI спецификации с самыми современными возможностями
        if USE_EXPERIMENTAL_PARSER:
            # Используем экспериментальный парсер если доступен
            try:
                os.environ["FASTMCP_EXPERIMENTAL_ENABLE_NEW_OPENAPI_PARSER"] = "true"
            except:
                pass
        
        self.mcp = FastMCP.from_openapi(
            openapi_spec=self.openapi_spec,
            client=self.http_client,
            name="🎮 Twitch API MCP Server (Powered by FastMCP)",
            route_maps=route_maps,
            # Добавляем глобальные теги
            tags={"twitch", "streaming", "api", "helix"}
        )
        
        # Применяем трансформации инструментов если включены
        if enable_transformations:
            transformations = self._create_tool_transformations()
            
            # Применяем трансформации к существующим инструментам
            for tool_name, transform_config in transformations.items():
                try:
                    # Получаем оригинальный инструмент (правильно с await)
                    tools = await self.mcp.get_tools()
                    if tool_name in tools:
                        original_tool = tools[tool_name]
                        
                        # Создаем трансформированный инструмент используя АКТУАЛЬНЫЙ API
                        transform_args = {}
                        if "arguments" in transform_config:
                            for arg_name, arg_config in transform_config["arguments"].items():
                                # Исправляем аргументы ArgTransform в соответствии с актуальным API
                                arg_transform_kwargs = {}
                                if "name" in arg_config:
                                    arg_transform_kwargs["name"] = arg_config["name"]
                                if "description" in arg_config:
                                    arg_transform_kwargs["description"] = arg_config["description"]
                                if "hide" in arg_config:
                                    arg_transform_kwargs["hide"] = arg_config["hide"]
                                if "default" in arg_config:
                                    arg_transform_kwargs["default"] = arg_config["default"]
                                if "default_factory" in arg_config:
                                    arg_transform_kwargs["default_factory"] = arg_config["default_factory"]
                                
                                transform_args[arg_name] = ArgTransform(**arg_transform_kwargs)
                        
                        # Используем АКТУАЛЬНЫЙ API Tool.from_tool
                        transformed_tool = Tool.from_tool(
                            original_tool,
                            name=transform_config.get("name", tool_name),
                            description=transform_config.get("description"),
                            meta=transform_config.get("meta", {}),
                            transform_args=transform_args if transform_args else None
                        )
                        
                        # Добавляем трансформированный инструмент
                        self.mcp.add_tool(transformed_tool)
                        
                        # Отключаем оригинальный инструмент
                        original_tool.disable()
                        
                        print(f"✅ Transformed tool: {tool_name} -> {transform_config.get('name', tool_name)}")
                        
                except Exception as e:
                    print(f"⚠️ Could not transform tool {tool_name}: {e}")
        
        # Добавляем дополнительные кастомные инструменты
        await self._add_custom_tools()
        
        return self.mcp
    
    async def _add_custom_tools(self):
        """Добавляет дополнительные кастомные инструменты"""
        
        @self.mcp.tool(
            name="get_twitch_token_info",
            description="Проверить информацию о текущем токене доступа Twitch API",
            tags={"auth", "utility"},
            meta={"category": "authentication", "difficulty": "easy"}
        )
        async def get_token_info(ctx: Context) -> Dict[str, Any]:
            """Получает информацию о текущем токене"""
            if not self.access_token:
                return {"error": "No access token provided"}
            
            try:
                # Проверяем токен через Twitch API
                response = await self.http_client.get("/oauth2/validate")
                if response.status_code == 200:
                    data = response.json()
                    await ctx.info(f"Token validated successfully for client: {data.get('client_id', 'unknown')}")
                    return {
                        "valid": True,
                        "client_id": data.get("client_id"),
                        "scopes": data.get("scopes", []),
                        "expires_in": data.get("expires_in")
                    }
                else:
                    await ctx.error(f"Token validation failed: {response.status_code}")
                    return {"valid": False, "error": "Token validation failed"}
            except Exception as e:
                await ctx.error(f"Error validating token: {str(e)}")
                return {"valid": False, "error": str(e)}
        
        @self.mcp.tool(
            name="twitch_quick_stats",
            description="Получить быструю статистику по пользователю Twitch (подписчики, просмотры, статус стрима)",
            tags={"users", "stats", "utility"},
            meta={"category": "analytics", "difficulty": "easy"}
        )
        async def quick_user_stats(username: str, ctx: Context) -> Dict[str, Any]:
            """Быстрая статистика по пользователю"""
            try:
                await ctx.info(f"Getting stats for user: {username}")
                
                # Получаем информацию о пользователе
                user_response = await self.http_client.get(f"/users?login={username}")
                if user_response.status_code != 200:
                    return {"error": f"User {username} not found"}
                
                user_data = user_response.json()["data"][0]
                user_id = user_data["id"]
                
                # Получаем информацию о стриме
                stream_response = await self.http_client.get(f"/streams?user_id={user_id}")
                stream_data = stream_response.json()["data"]
                is_live = len(stream_data) > 0
                
                # Получаем количество подписчиков
                followers_response = await self.http_client.get(f"/channels/followers?broadcaster_id={user_id}")
                followers_count = 0
                if followers_response.status_code == 200:
                    followers_count = followers_response.json().get("total", 0)
                
                stats = {
                    "username": user_data["display_name"],
                    "user_id": user_id,
                    "is_live": is_live,
                    "followers_count": followers_count,
                    "total_views": user_data["view_count"],
                    "created_at": user_data["created_at"],
                    "description": user_data["description"]
                }
                
                if is_live:
                    stream_info = stream_data[0]
                    stats.update({
                        "current_game": stream_info["game_name"],
                        "stream_title": stream_info["title"],
                        "viewer_count": stream_info["viewer_count"],
                        "stream_started": stream_info["started_at"]
                    })
                
                await ctx.info(f"Stats retrieved for {username}: Live={is_live}, Followers={followers_count}")
                return stats
                
            except Exception as e:
                await ctx.error(f"Error getting stats for {username}: {str(e)}")
                return {"error": str(e)}


def create_cli_parser() -> argparse.ArgumentParser:
    """Создает CLI парсер с поддержкой фильтрации по тегам"""
    parser = argparse.ArgumentParser(
        description="Twitch API MCP Server with advanced filtering",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Запустить сервер со всеми инструментами
  python mcp_twitch_server.py
  
  # Только инструменты для работы с каналами и пользователями
  python mcp_twitch_server.py --include-tags channels users
  
  # Исключить инструменты модерации
  python mcp_twitch_server.py --exclude-tags moderation
  
  # Запустить только поисковые инструменты
  python mcp_twitch_server.py --include-tags search
  
  # HTTP сервер на порту 8080
  python mcp_twitch_server.py --transport http --port 8080

Available tags: channels, users, streams, games, clips, search, analytics, moderation, content, followers, following, extensions
        """
    )
    
    parser.add_argument(
        '--client-id',
        help='Twitch Client ID (or set TWITCH_CLIENT_ID env var)'
    )
    
    parser.add_argument(
        '--access-token', 
        help='Twitch Access Token (or set TWITCH_ACCESS_TOKEN env var)'
    )
    
    parser.add_argument(
        '--include-tags',
        nargs='+',
        help='Include only tools with these tags'
    )
    
    parser.add_argument(
        '--exclude-tags',
        nargs='+', 
        help='Exclude tools with these tags'
    )
    
    parser.add_argument(
        '--no-transformations',
        action='store_true',
        help='Disable tool transformations (use original OpenAPI tools)'
    )
    
    parser.add_argument(
        '--transport',
        choices=['stdio', 'http', 'sse'],
        default='stdio',
        help='Transport protocol (default: stdio)'
    )
    
    parser.add_argument(
        '--host',
        default='127.0.0.1',
        help='Host for HTTP/SSE transport (default: 127.0.0.1)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=8000,
        help='Port for HTTP/SSE transport (default: 8000)'
    )
    
    parser.add_argument(
        '--list-tags',
        action='store_true',
        help='List all available tags and exit'
    )
    
    return parser


async def main():
    """Главная функция запуска сервера"""
    parser = create_cli_parser()
    args = parser.parse_args()
    
    # Если запрошен список тегов
    if args.list_tags:
        print("Available tags:")
        tags = [
            "channels - Channel management and information",
            "users - User information and profiles", 
            "streams - Live stream data",
            "games - Game and category information",
            "clips - Video clips management",
            "search - Search functionality",
            "analytics - Analytics and statistics",
            "moderation - Moderation tools",
            "content - Content management",
            "followers - Follower relationships",
            "following - Following relationships",
            "extensions - Twitch extensions"
        ]
        for tag in tags:
            print(f"  {tag}")
        return
    
    try:
        # Создаем сервер
        server = TwitchMCPServer(
            client_id=args.client_id,
            access_token=args.access_token
        )
        
        # Создаем MCP сервер с фильтрацией
        mcp = await server.create_server(
            include_tags=args.include_tags,
            exclude_tags=args.exclude_tags,
            enable_transformations=not args.no_transformations
        )
        
        # Выводим информацию о загруженных инструментах
        tools = await mcp.get_tools()
        print(f"\n🚀 Twitch MCP Server started with {len(tools)} tools")
        
        if args.include_tags:
            print(f"📌 Included tags: {', '.join(args.include_tags)}")
        if args.exclude_tags:
            print(f"🚫 Excluded tags: {', '.join(args.exclude_tags)}")
        
        print(f"🔧 Tool transformations: {'enabled' if not args.no_transformations else 'disabled'}")
        print(f"🌐 Transport: {args.transport}")
        
        if args.transport in ['http', 'sse']:
            print(f"🔗 URL: http://{args.host}:{args.port}")
        
        print("\nAvailable tools:")
        for tool_name in sorted(tools.keys()):
            tool = tools[tool_name]
            tags = getattr(tool, 'tags', set())
            tags_str = f"[{', '.join(tags)}]" if tags else ""
            print(f"  • {tool_name} {tags_str}")
        
        # Запускаем сервер с async методами
        if args.transport == 'stdio':
            await mcp.run_async()
        elif args.transport == 'http':
            await mcp.run_async(transport='http', host=args.host, port=args.port)
        elif args.transport == 'sse':
            await mcp.run_async(transport='sse', host=args.host, port=args.port)
            
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Проверяем специальные флаги перед инициализацией сервера
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h', '--list-tags']:
        asyncio.run(main())
    # Для совместимости с FastMCP CLI (без аргументов)
    elif len(sys.argv) == 1:
        # Создаем простой сервер для FastMCP CLI
        try:
            server = TwitchMCPServer()
            mcp = asyncio.run(server.create_server())
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    else:
        # Запускаем с полным CLI
        asyncio.run(main())
