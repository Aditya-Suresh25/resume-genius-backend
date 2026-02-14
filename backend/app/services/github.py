import httpx
import logging
from typing import Optional, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

async def fetch_github_data(github_url: str) -> str:
    """
    Fetches public GitHub data for a given user URL.
    Returns a formatted string summary for the LLM.
    """
    if not github_url:
        return ""

    username = github_url.rstrip("/").split("/")[-1]
    headers = {"Accept": "application/vnd.github.v3+json"}
    if settings.GITHUB_TOKEN:
        headers["Authorization"] = f"token {settings.GITHUB_TOKEN}"

    summary_parts = []

    async with httpx.AsyncClient() as client:
        try:
            # 1. Fetch User Profile
            user_resp = await client.get(f"https://api.github.com/users/{username}", headers=headers)
            if user_resp.status_code == 200:
                user_data = user_resp.json()
                summary_parts.append(f"User: {user_data.get('login')}")
                summary_parts.append(f"Name: {user_data.get('name', 'N/A')}")
                summary_parts.append(f"Bio: {user_data.get('bio', 'N/A')}")
                summary_parts.append(f"Public Repos: {user_data.get('public_repos', 0)}")
                summary_parts.append(f"Followers: {user_data.get('followers', 0)}")
            elif user_resp.status_code == 404:
                return f"GitHub User {username} not found."
            elif user_resp.status_code == 403:
                 return "GitHub API Rate Limit Exceeded. Using minimal data."

            # 2. Fetch Repositories (Fetch up to 100 to allow filtering)
            repos_resp = await client.get(
                f"https://api.github.com/users/{username}/repos?sort=pushed&per_page=100&type=owner",
                headers=headers
            )
            
            if repos_resp.status_code == 200:
                repos = repos_resp.json()
                
                # Filter Logic
                # 1. Start with non-forks with descriptions
                high_quality = [
                    r for r in repos 
                    if not r.get('fork') and r.get('description')
                ]
                
                # 2. Include forks if they have stars (indicates contribution/notable fork)
                notable_forks = [
                    r for r in repos 
                    if r.get('fork') and r.get('stargazers_count', 0) >= 2
                ]
                
                # 3. Fallback: If we have very few high quality repos, include any non-forks (even w/o desc)
                # or just recent ones to fill the gap.
                candidates = high_quality + notable_forks
                
                # Deduplicate just in case (though logic separates them)
                # Sort by stars (primary) and updated_at (secondary)
                sorted_repos = sorted(
                    candidates, 
                    key=lambda x: (x.get('stargazers_count', 0), x.get('updated_at', '')), 
                    reverse=True
                )
                
                # Selecting top candidates
                selected_repos = sorted_repos[:8]
                
                # FALLBACK: If < 3 selected, grab the most recent pushed repos regardless of stars/fork status
                # (to ensure we have *something* for the resume)
                if len(selected_repos) < 3:
                    remaining = [r for r in repos if r not in selected_repos]
                    recent_filler = sorted(remaining, key=lambda x: x.get('updated_at', ''), reverse=True)[:(5 - len(selected_repos))]
                    selected_repos.extend(recent_filler)

                summary_parts.append("\nTop Repositories (Filtered for Quality):")
                for repo in selected_repos:
                    name = repo.get('name')
                    stars = repo.get('stargazers_count', 0)
                    language = repo.get('language', 'Unknown')
                    desc = repo.get('description', 'No description')
                    url = repo.get('html_url')
                    # Add pushed_at to help LLM know recency
                    updated = repo.get('updated_at', '').split('T')[0]
                    summary_parts.append(f"- {name} ({language}): {stars} stars. Updated: {updated}. {desc} [Link: {url}]")
            
            # 3. Simple Contribution Proxy (Public Events)
            # Fetching accurate graph data requires querying /users/{username}/events and aggregating
            # For this MVP, we will rely on repo activity as a proxy.
            
        except httpx.RequestError as e:
            logger.error(f"GitHub API Connection Error: {e}")
            return f"Error fetching GitHub data: {str(e)}"

    return "\n".join(summary_parts)
