import os
import re
import pandas as pd

def extract_professor_name(professor_full):
    return re.match(r'^[^()]+', professor_full).group().strip()

def extract_course_mnemonic(course_full):
    return course_full.split(' |')[0].strip()

def avg_sentiment_df_creator():
    current_directory = os.path.dirname(os.path.abspath(__file__))
    reviews_data_path = os.path.join(current_directory, "reviews_data", "reviews_data_with_sentiment.csv")
    df = pd.read_csv(reviews_data_path)
    df["instructor_name_only"] = df["instructor"].apply(extract_professor_name)
    df["course_code_only"] = df["course"].apply(extract_course_mnemonic)
    avg_sentiment_df = df.groupby(["instructor_name_only", "course_code_only"])["sentiment_score"].mean().reset_index()
    return avg_sentiment_df

def query_average(df, professor, course):
    result = df[(df["instructor_name_only"] == professor) & (df["course_code_only"] == course)]
    if result.empty:
        print("No data found for the given professor and course.")
    else:
        print(f"Average sentiment score for {professor} in {course}: {result['sentiment_score'].values[0]:.2f}")

if __name__ == "__main__":
    avg_sentiment_df = avg_sentiment_df_creator()
    print(avg_sentiment_df)
    
    while True:
        professor = input("Enter professor name (or type 'exit' to quit): ")
        if professor.lower() == 'exit':
            break
        course = input("Enter course name (or type 'exit' to quit): ")
        if course.lower() == 'exit':
            break
        query_average(avg_sentiment_df, professor, course)