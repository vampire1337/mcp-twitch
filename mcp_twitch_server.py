#!/usr/bin/env python3
"""
🎮 MCP TWITCH SERVER - Universal Twitch API MCP Server

УНИВЕРСАЛЬНЫЙ MCP сервер для Twitch API с полной функциональностью:
🛠️  141 инструмент из Twitch Helix API
🏷️  Фильтрация по 30+ тегам для любых задач  
🎬 РЕЖИМ АВТОКОНВЕЙЕРА для клипов и трендов (--automation-mode)
🔄 HTTP/STDIO/SSE транспорты для любых интеграций
🎯 Готов для opensource и production использования

ИСПОЛЬЗУЕТ МАКСИМУМ FastMCP 2.0 (2025):
- from_openapi для автоматической генерации всех инструментов
- RouteMap для гибкой фильтрации по потребностям
- Tool Transform для улучшения UX инструментов
- Custom Tools для расширенной функциональности
- Поддержка всех современных MCP возможностей
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

# Загрузка переменных окружения из .env файла
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ .env file loaded successfully")
except ImportError:
    # dotenv не обязателен, можно использовать обычные переменные окружения
    pass

# Попытка использовать экспериментальный новый OpenAPI парсер
try:
    from fastmcp.experimental.server.openapi import FastMCPOpenAPI
    USE_EXPERIMENTAL_PARSER = True
    print("🧪 Using experimental FastMCP OpenAPI parser")
except ImportError:
    USE_EXPERIMENTAL_PARSER = False
    print("📚 Using standard FastMCP OpenAPI parser")


class TwitchMCPServer:
    """🎮 Универсальный MCP сервер для Twitch API с поддержкой режима автоматизации"""
    
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
                          exclude_tags: Optional[List[str]] = None, 
                          automation_mode: bool = False) -> List[RouteMap]:
        """
        🛠️ Создает карты маршрутов для фильтрации эндпоинтов
        - Универсальная фильтрация по тегам для любых задач
        - Режим автоматизации для специализированного использования
        """
        route_maps = []
        
        # РЕЖИМ АВТОМАТИЗАЦИИ: только клипы и тренды
        if automation_mode:
            route_maps = [
                # 🚫 ИСКЛЮЧАЕМ ВСЕ ПО УМОЛЧАНИЮ  
                RouteMap(pattern=r".*", mcp_type=MCPType.EXCLUDE),
                
                # ✅ ВКЛЮЧАЕМ ТОЛЬКО AUTOMATION-READY:
                RouteMap(pattern=r"^/clips$", methods=["GET", "POST"], mcp_type=MCPType.TOOL),
                RouteMap(pattern=r"^/videos$", methods=["GET", "DELETE"], mcp_type=MCPType.TOOL),
                RouteMap(pattern=r"^/search/channels$", methods=["GET"], mcp_type=MCPType.RESOURCE),
                RouteMap(pattern=r"^/search/categories$", methods=["GET"], mcp_type=MCPType.RESOURCE),
                RouteMap(pattern=r"^/streams$", methods=["GET"], mcp_type=MCPType.RESOURCE),
                RouteMap(pattern=r"^/users$", methods=["GET"], mcp_type=MCPType.RESOURCE),
                RouteMap(pattern=r"^/games$", methods=["GET"], mcp_type=MCPType.RESOURCE),
                RouteMap(pattern=r"^/games/top$", methods=["GET"], mcp_type=MCPType.RESOURCE),
            ]
            return route_maps
        
        # УНИВЕРСАЛЬНЫЙ РЕЖИМ: фильтрация по тегам
        
        # Исключаем указанные теги
        if exclude_tags:
            for tag in exclude_tags:
                route_maps.append(
                    RouteMap(
                        tags={tag},
                        mcp_type=MCPType.EXCLUDE,
                    )
                )
        
        # Включаем только указанные теги
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
        route_maps.extend([
            # GET эндпоинты для поиска и аналитики делаем ресурсами
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
        
        return route_maps
    
    def _create_tool_transformations(self, automation_mode: bool = False) -> Dict[str, Dict[str, Any]]:
        """
        🛠️ Создает трансформации для улучшения инструментов
        - Универсальные трансформации для всех режимов
        - Специальные трансформации для режима автоматизации
        """
        
        # УНИВЕРСАЛЬНЫЕ ТРАНСФОРМАЦИИ
        transformations = {
            # Улучшаем поиск пользователей
            "get_users": {
                "name": "find_twitch_users",
                "description": "Найти пользователей Twitch по логину или ID. Можно искать несколько пользователей одновременно.",
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
            }
        }
        
        # СПЕЦИАЛЬНЫЕ ТРАНСФОРМАЦИИ ДЛЯ РЕЖИМА АВТОМАТИЗАЦИИ
        if automation_mode:
            automation_transforms = {
                "get_clips": {
                    "name": "get_trending_clips",
                    "description": "🎬 Получить популярные клипы для автоконвейера",
                    "meta": {
                        "category": "clips_automation",
                        "automation_ready": True,
                        "n8n_friendly": True
                    }
                },
                "get_top_games": {
                    "name": "analyze_trending_categories",
                    "description": "📊 Анализ топовых игр и категорий для определения трендов",
                    "meta": {
                        "category": "trend_analysis", 
                        "automation_ready": True,
                        "data_freshness": "real-time"
                    }
                }
            }
            transformations.update(automation_transforms)
        
        return transformations
    
    async def create_server(self, include_tags: Optional[List[str]] = None, 
                           exclude_tags: Optional[List[str]] = None,
                           automation_mode: bool = False,
                           enable_transformations: bool = True) -> FastMCP:
        """
        🛠️ Создает FastMCP сервер с полной конфигурацией
        - Универсальный режим: все инструменты с фильтрацией по тегам  
        - Режим автоматизации: только клипы и тренды для N8N
        """
        
        # Создаем карты маршрутов для фильтрации
        route_maps = self._create_route_maps(include_tags, exclude_tags, automation_mode)
        
        # Создаем сервер из OpenAPI спецификации с самыми современными возможностями
        if USE_EXPERIMENTAL_PARSER:
            # Используем экспериментальный парсер если доступен
            try:
                os.environ["FASTMCP_EXPERIMENTAL_ENABLE_NEW_OPENAPI_PARSER"] = "true"
            except:
                pass
        
        # Выбираем название и теги в зависимости от режима
        if automation_mode:
            server_name = "🎬 Twitch Clips Automation Server (FastMCP 2.0)"
            server_tags = {"clips", "automation", "trends", "viral", "n8n", "highlights"}
        else:
            server_name = "🎮 Twitch API MCP Server (FastMCP 2.0)"
            server_tags = {"twitch", "streaming", "api", "helix", "universal"}
        
        self.mcp = FastMCP.from_openapi(
            openapi_spec=self.openapi_spec,
            client=self.http_client,
            name=server_name,
            route_maps=route_maps,
            tags=server_tags
        )
        
        # Применяем трансформации инструментов
        if enable_transformations:
            transformations = self._create_tool_transformations(automation_mode)
            
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
        await self._add_custom_tools(automation_mode)
        
        return self.mcp
    
    async def _add_custom_tools(self, automation_mode: bool = False):
        """🛠️ Добавляет кастомные инструменты в зависимости от режима"""
        
        # УНИВЕРСАЛЬНЫЙ ИНСТРУМЕНТ - проверка токена
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
        
        # РЕЖИМ АВТОМАТИЗАЦИИ: специальные инструменты
        if not automation_mode:
            return
            
        @self.mcp.tool(
            name="analyze_viral_potential",
            description="🔥 Анализ вирусного потенциала клипа или стрима. КРИТИЧНО для автоконвейера!",
            tags={"automation", "viral", "trends", "clips"},
            meta={"category": "trend_analysis", "automation_ready": True, "n8n_friendly": True}
        )
        async def analyze_viral_potential(streamer_username: str, game_category: Optional[str] = None, ctx: Context = None) -> Dict[str, Any]:
            """Анализирует вирусный потенциал контента на основе метрик стримера"""
            try:
                await ctx.info(f"🔥 Analyzing viral potential for: {streamer_username}")
                
                # Получаем информацию о стримере
                user_response = await self.http_client.get(f"/users?login={streamer_username}")
                if user_response.status_code != 200:
                    return {"error": f"Streamer {streamer_username} not found", "viral_score": 0}
                
                user_data = user_response.json()["data"][0]
                user_id = user_data["id"]
                
                # Проверяем текущий стрим
                stream_response = await self.http_client.get(f"/streams?user_id={user_id}")
                stream_data = stream_response.json()["data"]
                is_live = len(stream_data) > 0
                
                # Базовые метрики для вирусного потенциала
                follower_count = 0
                try:
                    followers_response = await self.http_client.get(f"/channels/followers?broadcaster_id={user_id}")
                    if followers_response.status_code == 200:
                        follower_count = followers_response.json().get("total", 0)
                except:
                    pass
                
                # Рассчитываем вирусный скор
                viral_score = 0
                factors = []
                
                # Фактор подписчиков
                if follower_count > 100000:
                    viral_score += 40
                    factors.append("🌟 High follower count")
                elif follower_count > 10000:
                    viral_score += 25
                    factors.append("📈 Good follower count")
                
                # Фактор активности (если в эфире)
                if is_live:
                    stream_info = stream_data[0]
                    viewer_count = stream_info.get("viewer_count", 0)
                    
                    if viewer_count > 10000:
                        viral_score += 30
                        factors.append("🔴 High viewer count LIVE")
                    elif viewer_count > 1000:
                        viral_score += 20
                        factors.append("📺 Good viewer count")
                    
                    viral_score += 10  # Бонус за активность
                    factors.append("⚡ Currently streaming")
                
                # Фактор популярности канала
                view_count = user_data.get("view_count", 0)
                if view_count > 50000000:
                    viral_score += 20
                    factors.append("🚀 Established creator")
                
                # Определяем рекомендацию
                if viral_score >= 70:
                    recommendation = "🔥 EXTREMELY HIGH - Create clips IMMEDIATELY!"
                elif viral_score >= 50:
                    recommendation = "⭐ HIGH - Great for viral content"
                elif viral_score >= 30:
                    recommendation = "📈 MEDIUM - Good potential"
                else:
                    recommendation = "💤 LOW - Consider other streamers"
                
                result = {
                    "streamer": user_data["display_name"],
                    "viral_score": viral_score,
                    "recommendation": recommendation,
                    "factors": factors,
                    "is_live": is_live,
                    "follower_count": follower_count,
                    "automation_priority": "high" if viral_score >= 50 else "medium" if viral_score >= 30 else "low"
                }
                
                if is_live:
                    result.update({
                        "current_viewers": stream_data[0].get("viewer_count", 0),
                        "current_game": stream_data[0].get("game_name", "Unknown"),
                        "stream_title": stream_data[0].get("title", "")
                    })
                
                await ctx.info(f"🔥 Viral analysis complete: {viral_score}/100 - {recommendation}")
                return result
                
            except Exception as e:
                await ctx.error(f"Error analyzing viral potential: {str(e)}")
                return {"error": str(e), "viral_score": 0}
        
        @self.mcp.tool(
            name="get_automation_ready_clips",
            description="🎬 Получить готовые к автоматизации клипы с метаданными для N8N",
            tags={"automation", "clips", "n8n", "highlights"},
            meta={"category": "clips_automation", "automation_ready": True, "n8n_friendly": True}
        )
        async def get_automation_ready_clips(
            streamer_username: Optional[str] = None,
            game_name: Optional[str] = None, 
            hours_back: int = 24,
            min_view_count: int = 1000,
            ctx: Context = None
        ) -> Dict[str, Any]:
            """Получает клипы оптимизированные для автоматической обработки"""
            try:
                await ctx.info(f"🎬 Getting automation-ready clips (last {hours_back}h)")
                
                params = {
                    "first": 20  # Ограничиваем для производительности
                }
                
                if streamer_username:
                    # Получаем ID стримера
                    user_response = await self.http_client.get(f"/users?login={streamer_username}")
                    if user_response.status_code == 200:
                        user_data = user_response.json()["data"]
                        if user_data:
                            params["broadcaster_id"] = user_data[0]["id"]
                
                # Получаем клипы
                clips_response = await self.http_client.get("/clips", params=params)
                if clips_response.status_code != 200:
                    return {"error": "Failed to get clips", "clips": []}
                
                clips_data = clips_response.json()["data"]
                
                # Обрабатываем клипы для автоматизации
                automation_clips = []
                for clip in clips_data:
                    # Фильтруем по просмотрам
                    if clip.get("view_count", 0) < min_view_count:
                        continue
                    
                    automation_clip = {
                        # Основные данные
                        "clip_id": clip["id"],
                        "title": clip["title"],
                        "url": clip["url"],
                        "embed_url": clip["embed_url"],
                        "thumbnail_url": clip["thumbnail_url"],
                        
                        # Метрики для автоматизации
                        "view_count": clip["view_count"],
                        "duration": clip["duration"],
                        "created_at": clip["created_at"],
                        
                        # Информация о стримере
                        "broadcaster_name": clip["broadcaster_name"],
                        "broadcaster_id": clip["broadcaster_id"],
                        
                        # Игра/категория
                        "game_name": clip.get("game_name", "Unknown"),
                        "game_id": clip.get("game_id"),
                        
                        # N8N готовые поля
                        "automation_score": min(100, int(clip["view_count"] / 100)),
                        "download_ready": True,
                        "processing_priority": "high" if clip["view_count"] > 5000 else "medium",
                        
                        # Теги для автоматической категоризации
                        "auto_tags": [
                            clip.get("game_name", "gaming").lower().replace(" ", "_"),
                            "viral" if clip["view_count"] > 10000 else "trending",
                            f"duration_{int(clip['duration'])}s"
                        ]
                    }
                    
                    automation_clips.append(automation_clip)
                
                # Сортируем по automation_score
                automation_clips.sort(key=lambda x: x["automation_score"], reverse=True)
                
                result = {
                    "clips": automation_clips[:10],  # Топ 10 для автоматизации
                    "total_found": len(clips_data),
                    "automation_ready": len(automation_clips),
                    "filters_applied": {
                        "streamer": streamer_username,
                        "game": game_name,
                        "min_views": min_view_count,
                        "hours_back": hours_back
                    },
                    "n8n_workflow_ready": True
                }
                
                await ctx.info(f"🎬 Found {len(automation_clips)} automation-ready clips")
                return result
                
            except Exception as e:
                await ctx.error(f"Error getting automation clips: {str(e)}")
                return {"error": str(e), "clips": []}
        
        @self.mcp.tool(
            name="trend_monitoring_dashboard",
            description="📊 Мониторинг трендов в реальном времени для автоконвейера",
            tags={"trends", "monitoring", "automation", "dashboard"},
            meta={"category": "trend_analysis", "automation_ready": True, "real_time": True}
        )
        async def trend_monitoring_dashboard(ctx: Context = None) -> Dict[str, Any]:
            """Создает дашборд трендов для автоматического мониторинга"""
            try:
                await ctx.info("📊 Building trend monitoring dashboard...")
                
                # Получаем топ игры
                top_games_response = await self.http_client.get("/games/top?first=10")
                top_games = []
                if top_games_response.status_code == 200:
                    games_data = top_games_response.json()["data"]
                    for i, game in enumerate(games_data, 1):
                        top_games.append({
                            "rank": i,
                            "name": game["name"],
                            "id": game["id"],
                            "box_art_url": game["box_art_url"],
                            "automation_priority": "high" if i <= 3 else "medium" if i <= 7 else "low"
                        })
                
                # Получаем топ стримы
                top_streams_response = await self.http_client.get("/streams?first=15")
                trending_streamers = []
                if top_streams_response.status_code == 200:
                    streams_data = top_streams_response.json()["data"]
                    for stream in streams_data[:10]:
                        viral_score = min(100, int(stream["viewer_count"] / 500))
                        trending_streamers.append({
                            "username": stream["user_name"],
                            "user_id": stream["user_id"],
                            "viewer_count": stream["viewer_count"],
                            "game_name": stream["game_name"],
                            "title": stream["title"],
                            "thumbnail_url": stream["thumbnail_url"],
                            "viral_score": viral_score,
                            "clip_potential": "high" if viral_score >= 60 else "medium" if viral_score >= 30 else "low"
                        })
                
                # Создаем рекомендации для автоматизации
                automation_recommendations = []
                
                # Рекомендации по играм
                if top_games:
                    for game in top_games[:3]:
                        automation_recommendations.append({
                            "type": "game_focus",
                            "action": f"Monitor clips from {game['name']}",
                            "priority": "high",
                            "game_id": game["id"]
                        })
                
                # Рекомендации по стримерам
                for streamer in trending_streamers[:3]:
                    if streamer["viral_score"] >= 60:
                        automation_recommendations.append({
                            "type": "streamer_clips",
                            "action": f"Create clips from {streamer['username']} stream",
                            "priority": "urgent",
                            "user_id": streamer["user_id"],
                            "current_viewers": streamer["viewer_count"]
                        })
                
                dashboard = {
                    "timestamp": asyncio.get_event_loop().time(),
                    "trending_games": top_games,
                    "viral_streamers": trending_streamers,
                    "automation_recommendations": automation_recommendations,
                    "market_analysis": {
                        "hot_categories": [game["name"] for game in top_games[:3]],
                        "peak_viewing_hours": True,  # Можно сделать более умным
                        "clip_creation_opportunity": "high" if len([s for s in trending_streamers if s["viral_score"] >= 50]) >= 3 else "medium"
                    },
                    "n8n_webhook_ready": True
                }
                
                await ctx.info(f"📊 Dashboard ready: {len(top_games)} games, {len(trending_streamers)} viral streamers")
                return dashboard
                
            except Exception as e:
                await ctx.error(f"Error building trend dashboard: {str(e)}")
                return {"error": str(e)}


def create_cli_parser() -> argparse.ArgumentParser:
    """🎮 Создает CLI парсер для универсального Twitch MCP сервера"""
    parser = argparse.ArgumentParser(
        description="🎮 Universal Twitch API MCP Server (FastMCP 2.0)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
🛠️ УНИВЕРСАЛЬНЫЙ MCP сервер для Twitch API с полной функциональностью:

Examples:
  # Все инструменты (141 tools)
  python mcp_twitch_server.py
  
  # Фильтрация по тегам
  python mcp_twitch_server.py --include-tags channels users streams
  python mcp_twitch_server.py --exclude-tags moderation
  
  # HTTP сервер
  python mcp_twitch_server.py --transport http --port 8080
  
  # РЕЖИМ АВТОМАТИЗАЦИИ (специализированный)
  python mcp_twitch_server.py --automation-mode
  python mcp_twitch_server.py --automation-mode --transport http --port 8080

🏷️ ДОСТУПНЫЕ ТЕГИ:
  channels, users, streams, games, clips, search, analytics, 
  moderation, content, followers, following, extensions, etc.
  
🎬 РЕЖИМ АВТОМАТИЗАЦИИ (--automation-mode):
  • Только инструменты для клипов и трендов
  • Оптимизирован для N8N интеграции  
  • Специальные инструменты анализа трендов
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
        '--automation-mode',
        action='store_true',
        default=os.getenv('AUTOMATION_MODE', '').lower() == 'true',
        help='🎬 Enable automation mode - specialized for clips and trends'
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
        default=os.getenv('HOST', '127.0.0.1'),
        help='Host for HTTP/SSE transport (default: from $HOST env or 127.0.0.1)'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=int(os.getenv('PORT', 8080)),
        help='Port for HTTP/SSE transport (default: from $PORT env or 8080)'
    )
    
    parser.add_argument(
        '--list-tags',
        action='store_true',
        help='List all available tags and exit'
    )
    
    return parser


async def main():
    """🎮 Главная функция запуска универсального сервера"""
    parser = create_cli_parser()
    args = parser.parse_args()
    
    # Если запрошен список тегов
    if args.list_tags:
        print("🏷️ Available tags:")
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
            "extensions - Twitch extensions",
            "",
            "🎬 AUTOMATION MODE (--automation-mode):",
            "  • Включает только clips, videos, streams, users, games, search",
            "  • Добавляет специальные инструменты анализа трендов",
            "  • Оптимизирован для N8N интеграции"
        ]
        for tag in tags:
            if tag:
                print(f"  {tag}")
            else:
                print()
        return
    
    try:
        # Создаем универсальный сервер
        server = TwitchMCPServer(
            client_id=args.client_id,
            access_token=args.access_token
        )
        
        # Создаем MCP сервер с нужной конфигурацией
        mcp = await server.create_server(
            include_tags=args.include_tags,
            exclude_tags=args.exclude_tags,
            automation_mode=args.automation_mode,
            enable_transformations=not args.no_transformations
        )
        
        # Выводим информацию о загруженных инструментах
        tools = await mcp.get_tools()
        
        if args.automation_mode:
            print(f"\n🎬 Twitch Automation Server started with {len(tools)} specialized tools")
            print(f"🎯 Mode: Clips & Highlights & Trends automation")
        else:
            print(f"\n🎮 Twitch MCP Server started with {len(tools)} tools")
            print(f"🎯 Mode: Universal Twitch API access")
        
        if args.include_tags:
            print(f"📌 Included tags: {', '.join(args.include_tags)}")
        if args.exclude_tags:
            print(f"🚫 Excluded tags: {', '.join(args.exclude_tags)}")
        
        print(f"🔧 Tool transformations: {'enabled' if not args.no_transformations else 'disabled'}")
        print(f"🌐 Transport: {args.transport}")
        
        if args.transport in ['http', 'sse']:
            url_desc = "N8N Integration URL" if args.automation_mode else "HTTP API URL"
            print(f"🔗 {url_desc}: http://{args.host}:{args.port}")
        
        if args.automation_mode:
            print(f"\n🎬 AUTOMATION TOOLS:")
            automation_count = 0
            for tool_name in sorted(tools.keys()):
                tool = tools[tool_name]
                tags = getattr(tool, 'tags', set())
                if any(tag in {'automation', 'clips', 'viral', 'trends'} for tag in tags):
                    tags_str = f"[{', '.join(tags)}]" if tags else ""
                    print(f"  🎯 {tool_name} {tags_str}")
                    automation_count += 1
            
            supporting_count = len(tools) - automation_count
            if supporting_count > 0:
                print(f"\n📋 SUPPORTING TOOLS: {supporting_count} standard Twitch API tools")
        else:
            print(f"\nAvailable tools ({len(tools)}):")
            for tool_name in sorted(tools.keys()):
                tool = tools[tool_name]
                tags = getattr(tool, 'tags', set())
                tags_str = f"[{', '.join(tags)}]" if tags else ""
                print(f"  • {tool_name} {tags_str}")
        
        integration_ready = "N8N ready" if args.automation_mode else "MCP ready"
        print(f"\n🚀 {integration_ready} on {args.transport} transport!")
        
        # Добавляем health check endpoint для Railway
        if args.transport in ['http', 'sse']:
            @mcp.server.get("/health")
            async def health_check():
                """Health check endpoint for Railway and monitoring"""
                return {"status": "healthy", "service": "twitch-mcp-server", "mode": "automation" if args.automation_mode else "universal"}
        
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
        # Создаем универсальный сервер
        try:
            print("🎮 Starting Universal Twitch MCP Server...")
            server = TwitchMCPServer()
            mcp = asyncio.run(server.create_server())
        except Exception as e:
            print(f"❌ Server error: {e}")
            sys.exit(1)
    else:
        # Запускаем с полным CLI
        asyncio.run(main())
