# ============================================================
# INTEGRITY SCOUT ENGINE — Weekly Job Hunter
# Runs every Monday morning via GitHub Actions
# Target: 20-30 quality leads per week
# ============================================================

import requests
from datetime import datetime

# ============================================================
# CONFIG — API KEYS
# ============================================================
SERPER_API_KEY = "e25cf8c7b3b06b8738aef86bfb72b7ba91db9065"
SUPABASE_URL   = "https://qdtnucxuaocvlodlydys.supabase.co"
SUPABASE_KEY   = "sb_publishable_r8szbAeXZmH5imyllluObw_LMcW3Ggn"
TABLE          = "jobs_tracker"

# ============================================================
# HUNT CONFIG — Lean and surgical for 20-30 results/week
# Tweak these anytime to change what gets searched
# ============================================================
TITLES = [
    "IT Support Specialist",
    "IT Support Engineer",
    "Desktop Support Technician",
    "IT Support Analyst",
]

LOCATIONS = [
    "Chicago",
    "Remote",
]

# High-quality platforms only — keeps result volume tight
PLATFORMS = [
    "linkedin.com/jobs",
    "indeed.com",
    "glassdoor.com",
    "dice.com",
]

# Results per query — 2-3 per combo hits our 20-30 target
# 4 titles x 2 locations x 4 platforms x 2 results = ~64 candidates
# After duplicates: expect 20-30 unique new leads
RESULTS_PER_QUERY = 3

# Hard stop — won't save more than this per run
# Keeps your weekly list manageable
WEEKLY_CAP = 30


# ============================================================
# SUPABASE — Check if job already exists
# ============================================================
def check_if_exists(url):
    endpoint = f"{SUPABASE_URL}/rest/v1/{TABLE}?job_url=eq.{requests.utils.quote(url, safe='')}&select=id"
    headers  = {
        "apikey":        SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}"
    }
    try:
        response = requests.get(endpoint, headers=headers)
        return len(response.json()) > 0
    except Exception as e:
        print(f"⚠️  DB check failed: {e}")
        return False  # Assume it doesn't exist so we don't lose leads


# ============================================================
# SUPABASE — Save a new job to the vault
# ============================================================
def save_to_vault(job_title, company, url, platform, week_of):
    endpoint = f"{SUPABASE_URL}/rest/v1/{TABLE}"
    headers  = {
        "apikey":        SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type":  "application/json",
        "Prefer":        "return=minimal"
    }
    payload = {
        "job_title":    job_title,
        "company":      company,
        "job_url":      url,
        "platform":     platform,
        "status":       "New",
        "salary_range": "N/A",
        "date_applied": datetime.now().isoformat(),
        "notes":        f"Auto-sourced | Week of {week_of}"
    }
    try:
        response = requests.post(endpoint, headers=headers, json=payload)
        if response.status_code in [200, 201]:
            print(f"  ✅ VAULTED: {job_title} — {company}")
            return True
        else:
            print(f"  ❌ Save error {response.status_code}: {response.text}")
            return False
    except Exception as e:
        print(f"  ⚠️  Save failed: {e}")
        return False


# ============================================================
# SERPER — Search Google for jobs
# ============================================================
def search_jobs(query, num_results):
    headers = {
        "X-API-KEY":    SERPER_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "q":   query,
        "num": num_results
    }
    try:
        response = requests.post(
            "https://google.serper.dev/search",
            headers=headers,
            json=payload
        )
        if response.status_code == 200:
            return response.json().get("organic", [])
        else:
            print(f"  ❌ Serper error {response.status_code}: {response.text}")
            return []
    except Exception as e:
        print(f"  ⚠️  Search failed: {e}")
        return []


# ============================================================
# MAIN — Weekly Hunt
# ============================================================
def run_weekly_hunt():
    week_of    = datetime.now().strftime("%B %d, %Y")
    total_queries  = len(TITLES) * len(LOCATIONS) * len(PLATFORMS)
    vaulted    = 0
    skipped    = 0
    searched   = 0

    print("=" * 55)
    print(f"  INTEGRITY SCOUT ENGINE — Weekly Hunt")
    print(f"  Week of {week_of}")
    print(f"  {total_queries} queries | Cap: {WEEKLY_CAP} leads")
    print("=" * 55)

    for title in TITLES:
        for location in LOCATIONS:
            for platform in PLATFORMS:

                # Stop early if we've hit our weekly cap
                if vaulted >= WEEKLY_CAP:
                    print(f"\n🏁 Weekly cap of {WEEKLY_CAP} reached. Stopping early.")
                    break

                query = f"{title} {location} site:{platform}"
                searched += 1
                print(f"\n[{searched}/{total_queries}] Searching: {query}")

                results = search_jobs(query, RESULTS_PER_QUERY)

                if not results:
                    print("  — No results returned.")
                    continue

                for job in results:
                    if vaulted >= WEEKLY_CAP:
                        break

                    job_url = job.get("link")
                    job_title = job.get("title", title)
                    # Serper puts company info in the snippet
                    company = job.get("snippet", "Unknown Company")[:80]

                    if not job_url:
                        continue

                    if check_if_exists(job_url):
                        skipped += 1
                        print(f"  ⏭️  SKIP (duplicate): {job_title}")
                    else:
                        saved = save_to_vault(
                            job_title=job_title,
                            company=company,
                            url=job_url,
                            platform=platform,
                            week_of=week_of
                        )
                        if saved:
                            vaulted += 1

            else:
                continue
            break  # Cascade the weekly cap break upward
        else:
            continue
        break

    # ---- SUMMARY ----
    print("\n" + "=" * 55)
    print(f"  HUNT COMPLETE — Week of {week_of}")
    print(f"  Queries run:      {searched}")
    print(f"  New leads vaulted: {vaulted}")
    print(f"  Duplicates skipped: {skipped}")
    print(f"  Open your dashboard to review your leads.")
    print("=" * 55 + "\n")


# ============================================================
# RUN
# ============================================================
if __name__ == "__main__":
    run_weekly_hunt()
