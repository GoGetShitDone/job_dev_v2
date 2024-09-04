import csv
import os


def save_to_file(file_name, jobs):
    """검색된 일자리 데이터를 CSV 파일로 저장"""
    with open(f"{file_name}.csv", "w", newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["Position", "Company", "Salary",
                        "Skills", "Source", "URL"])
        for job in jobs:
            writer.writerow([
                job['position'], job['company'], job.get('salary', 'N/A'),
                ', '.join(job['skills']), job['source'], job['link']
            ])
    print(f"Saved {len(jobs)} jobs to {file_name}.csv")


def load_jobs_from_csv(file_name):
    """CSV 파일에서 일자리 데이터를 불러오기"""
    jobs = []
    file_path = f"{file_name}.csv"
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"No file found for {file_name}")

    with open(file_path, newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            jobs.append({
                'position': row['Position'],
                'company': row['Company'],
                'salary': row['Salary'],
                'skills': row['Skills'].split(', '),
                'source': row['Source'],
                'link': row['URL']
            })
    print(f"Loaded {len(jobs)} jobs from {file_name}.csv")
    return jobs
