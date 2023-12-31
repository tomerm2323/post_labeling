import os
from PIL import Image
import streamlit as st
import pandas as pd
from st_files_connection import FilesConnection
import boto3
import toml
import time
from io import BytesIO

from botocore.exceptions import NoCredentialsError
import s3fs
# Function to create a custom labeling component
def get_client():

    # Load AWS credentials from the TOML file
    with open("secrets.toml", "r") as toml_file:
        config = toml.load(toml_file)

    aws_access_key = config["aws"]["AWS_ACCESS_KEY_ID"]
    aws_secret_key = config["aws"]["AWS_SECRET_ACCESS_KEY"]
    aws_region = config["aws"]["AWS_DEFAULT_REGION"]

    # Create an S3 client using the credentials
    s3 = boto3.client(
        "s3",
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key,
        region_name=aws_region
    )
    return s3

def get_images():
    bucket_name = "streamlit-posts-labeling"
    folder_name = 'images'
    s3 = get_client()
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=folder_name)
    images_urls = [obj['Key'] for obj in response.get('Contents', []) if
              obj['Key'].lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))]

    return images_urls
def get_videos():
    bucket_name = "streamlit-posts-labeling"
    folder_name = 'videos'
    s3 = get_client()
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=folder_name)
    videos_urls = [obj['Key'] for obj in response.get('Contents', []) if
              obj['Key'].lower().endswith('mp4')]

    return videos_urls
def get_posts_files():
    bucket_name = "streamlit-posts-labeling"
    folder_name = 'text'
    s3 = get_client()
    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=folder_name)
    csv_files = [obj['Key'] for obj in response.get('Contents', []) if
              obj['Key'].lower().endswith('csv')]
    dataframes = []
    for csv_file in csv_files:
        obj = s3.get_object(Bucket=bucket_name, Key=csv_file)
        dataframe = pd.read_csv(obj['Body'])
        dataframes.append(dataframe)

    return dataframes

def load_csv_to_dataframe(bucket_name, csv_key):
    s3 = boto3.client('s3')
    obj = s3.get_object(Bucket=bucket_name, Key=csv_key)
    dataframe = pd.read_csv(obj['Body'])
    return dataframe
def post_label_component(data, current_row):

    st.write(f"**Text:** {data.iloc[current_row, 0]}")
    label = st.text_input(f"Enter label for post {current_row + 1}:", key=f"label_{current_row}")

    return label

def image_label_component(image_url,current_image,bucket_name):
    s3 = get_client()
    img_data = s3.get_object(Bucket=bucket_name, Key=image_url)
    img = Image.open(BytesIO(img_data['Body'].read()))
    st.image(img, caption="Image from S3", use_column_width=True)
    label = st.text_input(f"Enter label for image {current_image}:", key=f"label_image_{current_image}")
    return label
def video_label_component(video_url,current_video,bucket_name):
    s3 = boto3.client('s3')
    video_data = s3.get_object(Bucket=bucket_name, Key=video_url)
    video_bytes = video_data['Body'].read()

    st.video(video_bytes, format="video/mp4")  # Specify the video format if known

    label = st.text_input(f"Enter label for video {current_video}:", key=f"label_video_{current_video}")
    return label
@st.experimental_memo
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8')

def upload_data_to_s3(data, bucket_name, s3_path):
    s3 = boto3.client('s3')
    try:
        s3.put_object(Bucket=bucket_name, Key=s3_path, Body=data)
        return True
    except NoCredentialsError:
        st.error("AWS credentials not available. Please configure AWS credentials.")
        return False
# Main Streamlit app
def main():

    st.title(f"Labeling Form")

    st.markdown("How to label? first let's get to know our labels")
    st.markdown("1. :violet[Non relevant] - Data that is not the war related at all.")
    st.markdown("2. :green[Relevant and pro Israel] - Data that shows Israel in a good light regarding the war.")
    st.markdown("3. :red[Relevant and pro Hamas] - Data that shows Israel in a bad light or Hamas in a good light regarding the war.")
    st.markdown("4. :gray[Relevant and neutral] - Data that related to the war but takes not obvious side.")

    st.markdown("Please label each data item(image, text etc...) as it corresponding index in the explanation above.")
    st.write("**EXAMPLE**")
    st.write("post - Israel killing children's will be labeled as 3 because it's against Israel and regarding the war.\n"
             ""
             ""
             "")


    label_dict = {"post" : {},"image": {}, "video": {}}
    bucket_name = "streamlit-posts-labeling"


    st.subheader("**Text labeling**")
    st.write("")
    posts_files = get_posts_files()
    for posts_file in posts_files:
        for current_row in range(len(posts_file)):
            label = post_label_component(posts_file, current_row)
            label_dict["post"][posts_file.iloc[current_row, 0]] = label

    st.subheader("**Image labeling**")
    st.write("")
    images_urls = get_images()
    for current_image, image_url in enumerate(images_urls):
        label = image_label_component(image_url,current_image,bucket_name)
        label_dict['image'][f"image_{current_image}_{time.time()}"] = label
    videos_urls = get_videos()

    st.subheader("**Video labeling**")
    st.write("")
    for current_video, video_url in enumerate(videos_urls):
        label = video_label_component(video_url, current_video, bucket_name)
        label_dict['video'][f"video_{current_video}_{time.time()}"] = label

    labeled_data = pd.DataFrame.from_dict(label_dict)
    st.subheader("Please review your labels and submit")

    st.write("**Submit**")

    data_to_submit = convert_df(labeled_data)
    # If the user clicks the "Submit" button
    if st.button("Submit"):
        s3_bucket_name = 'streamlit-posts-labeling'
        s3_data_path = 'labeled/labeled.csv'

        if upload_data_to_s3(data_to_submit, s3_bucket_name, s3_data_path):
            st.success(f"Data submitted and uploaded to S3: s3://{s3_bucket_name}/labeled/{s3_data_path}")
        else:
            st.error("Failed to upload the data to S3.")

    st.write("Labeled Data:")
    st.write(labeled_data)

if __name__ == "__main__":
    main()
