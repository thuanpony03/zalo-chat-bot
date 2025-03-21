#!/usr/bin/env python3
"""
Test script for tour processing functionality
"""
import asyncio
import sys
import os

# Add the parent directory to the path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.tour_processor import tour_processor

async def test_tour_queries():
    """Test various tour queries"""
    test_queries = [
        "Tôi muốn đi tour private tới Nhật Bản",
        "Tour riêng đi Hàn Quốc 5 người",
        "Cho tôi báo giá tour private đi Châu Âu 7 ngày",
        "Tour riêng đi Thái Lan 3 người 4 ngày",
        "Tour tự túc đi Singapore",
    ]
    
    context = {}
    for query in test_queries:
        print(f"\n--- Testing query: '{query}' ---")
        response, context = await tour_processor.process_tour_query(query, context)
        print(f"Response: {response}")
        print(f"Context: {context}")

if __name__ == "__main__":
    print("Testing Tour Processor...")
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_tour_queries())
