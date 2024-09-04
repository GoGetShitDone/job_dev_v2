from flask import Flask, render_template, request, jsonify, send_file, redirect
from scraper import scrap_berlin_job_descriptions, scrap_web3_job_descriptions
from utils import init_cache
from file import save_to_file
import asyncio
import os

app = Flask(__name__)

init_cache()
db = {}  # 검색된 데이터를 저장할 캐시


@app.route("/")
def home():
    return render_template('home.html')


@app.route("/search")
def search():
    keyword = request.args.get("keyword")
    return render_template('search.html', keyword=keyword)


@app.route("/api/search")
async def api_search():
    keyword = request.args.get("keyword")
    if not keyword:
        return jsonify({"results": []})

    print(f"Searching for keyword: {keyword}")

    loop = asyncio.get_event_loop()
    berlin_results = await loop.run_in_executor(None, scrap_berlin_job_descriptions, keyword)
    web3_results = await loop.run_in_executor(None, scrap_web3_job_descriptions, keyword)

    results = berlin_results + web3_results

    formatted_results = []
    for job in results:
        formatted_results.append({
            "position": job.position,
            "company": job.company,
            "salary": job.salary,
            "skills": job.skills,
            "source": job.source,
            "link": job.link
        })

    db[keyword] = formatted_results  # 캐시에 저장
    print(f"Found {len(formatted_results)} results")
    return jsonify({"results": formatted_results})


@app.route("/test_scraper")
def test_scraper():
    keyword = "python"
    berlin_results = scrap_berlin_job_descriptions(query=keyword)
    web3_results = scrap_web3_job_descriptions(tag=keyword)
    return jsonify({
        "berlin_count": len(berlin_results),
        "web3_count": len(web3_results),
        "berlin_sample": str(berlin_results[:1]),
        "web3_sample": str(web3_results[:1])
    })


@app.route("/export")
def export():
    keyword = request.args.get("keyword")
    if not keyword or keyword not in db:
        return redirect("/")

    save_to_file(keyword, db[keyword])  # 파일 저장
    return send_file(f"{keyword}.csv", as_attachment=True)  # CSV 파일 다운로드


if __name__ == "__main__":
    app.run(debug=True)
