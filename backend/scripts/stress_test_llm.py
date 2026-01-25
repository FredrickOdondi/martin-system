#!/usr/bin/env python3
"""
Stress Test Script for Self-Hosted LLMs
Simulates 50 consecutive meeting summary requests to test stability and context.
"""
import time
import asyncio
import sys
import os

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.llm_service import get_llm_service
from app.core.config import settings

async def test_single_meeting(i, llm):
    start = time.time()
    prompt = f"Summarize this meeting transcript for meeting #{i}: [SIMULATED MEETING CONTENT FOR ECOWAS SUMMIT]"
    try:
        response = await asyncio.to_thread(llm.chat, prompt)
        latency = time.time() - start
        print(f"✅ Meeting {i} done in {latency:.2f}s. Response length: {len(response)}")
        return latency
    except Exception as e:
        print(f"❌ Meeting {i} failed: {e}")
        return None

async def main():
    print(f"--- Starting Stress Test on Provider: {settings.LLM_PROVIDER} ---")
    print(f"Model: {settings.CUSTOM_LLM_MODEL if settings.LLM_PROVIDER == 'custom' else 'N/A'}")
    print(f"Target URL: {settings.CUSTOM_LLM_BASE_URL}")
    
    llm = get_llm_service()
    
    tasks = 50
    latencies = []
    
    print(f"Running {tasks} consecutive requests...")
    
    for i in range(1, tasks + 1):
        lat = await test_single_meeting(i, llm)
        if lat:
            latencies.append(lat)
        
        # Small delay to prevent network saturation, but keep pressure on GPU
        await asyncio.sleep(0.5)

    if latencies:
        avg = sum(latencies) / len(latencies)
        print(f"\n--- Results ---")
        print(f"Total Successful: {len(latencies)}/{tasks}")
        print(f"Average Latency: {avg:.2f}s")
        print(f"Min Latency: {min(latencies):.2f}s")
        print(f"Max Latency: {max(latencies):.2f}s")
    else:
        print("No successful requests.")

if __name__ == "__main__":
    asyncio.run(main())
