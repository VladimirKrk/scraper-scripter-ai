from src.collectors.local_extractor import run_local_analysis
from src.collectors.web_scraper import run_web_scraping
from src.analysis.merger import run_merge
from src.ai_engine.vector_store import rebuild_knowledge_base
def main():
    print("===Starting AI Pipeline===")

    #running local file analysis
    run_local_analysis()
    #run web scraping
    run_web_scraping()
    #print("Staring analysis and merging")
    run_merge()
    print("Starting AI learning")
    rebuild_knowledge_base()

    print("Done, now start up the app.py")

if __name__ == "__main__":
    main()