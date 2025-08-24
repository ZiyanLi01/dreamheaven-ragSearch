#!/usr/bin/env python3
import asyncio
from dotenv import load_dotenv
from search_engine import SearchEngine
from database import DatabaseManager
from config import Config
from openai import AsyncOpenAI
from intent_extractor import IntentExtractor

async def debug_semantic():
    load_dotenv()
    config = Config()
    db_manager = DatabaseManager(config.DATABASE_URL)
    await db_manager.initialize()
    openai_client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)
    search_engine = SearchEngine(db_manager, openai_client)
    
    results = await search_engine.search('Give me a short-term rental in downtown that allows pets', limit=1)
    result = results.items[0]
    
    print(f'Title: {result.title}')
    print(f'City: {result.city}')
    print(f'State: {result.state}')
    print(f'Neighborhood: {result.neighborhood}')
    print(f'Address: {result.address}')
    
    # Check intent
    intent_extractor = IntentExtractor()
    intent = intent_extractor.extract_intent('Give me a short-term rental in downtown that allows pets')
    print(f'\nIntent:')
    print(f'  city: {intent.city}')
    print(f'  state: {intent.state}')
    print(f'  neighborhood: {intent.neighborhood}')
    
    await db_manager.close()

if __name__ == "__main__":
    asyncio.run(debug_semantic())
