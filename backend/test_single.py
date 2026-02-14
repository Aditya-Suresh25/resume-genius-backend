
import asyncio
import httpx

async def test_single():
    url = "http://127.0.0.1:8000/api/v1/analyze"
    # Using a known valid github
    payload = {
        "linkedin_url": None,
        "github_url": "https://github.com/torvalds"
    }
    
    print(f"Sending POST to {url}...")
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(url, json=payload, timeout=60)
            if resp.status_code == 200:
                print("Success! JSON schema valid.")
                # print(resp.json()) # Too verbose
            else:
                print(f"Failed: {resp.status_code} - {resp.text}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_single())
