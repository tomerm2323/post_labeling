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
def labeling_component(data, current_row):

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
def video_label_component(path,current_video):
    video_file = open(path, 'rb')
    video_bytes = video_file.read()
    st.video(video_bytes)
    label = st.text_input(f"Enter label for video {current_video}:", key=f"label_video_{current_video}")
    return label
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
    st.write("post - Israel killing children's will be labeled as 3 because it's against Israel and regarding the war.")


    label_dict = {"post" : {},"image": {}, "video": {}}
    posts_files = get_posts_files()
    for posts_file in posts_files:
        for current_row in range(len(posts_file)):
            label = labeling_component(posts_file, current_row)
            label_dict["post"][posts_file.iloc[current_row, 0]] = label

    images_urls = get_images()
    for current_image, image_url in enumerate(images_urls):
        label = image_label_component(image_url,current_image,"streamlit-posts-labeling")
        label_dict['image'][f"image_{current_image}_{time.time()}"] = label

    # for current_video, path in enumerate(os.listdir(video_data_path)):
    #     label = video_label_component(video_data_path + "/" + path, current_video)
    #     data.loc[len(data.index)] = f"video_{current_video}"
    #     labels.append(label)
    #
    #
    # Check if the number of labels provided matches the number of rows
    # if len() != num_entries + num_images:
    #     st.error("Please provide labels for all before submitting.")
    # if len(labels) != num_entries + len(os.listdir(image_data_path)) + len(os.listdir(video_data_path))  :
    #     st.error("Please provide labels for all rows before submitting.")
    # else:
    # Save the labeled data to a new CSV file

    labeled_data = pd.DataFrame.from_dict(label_dict)
    st.title("Please review your labels and submit")
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

    st.write("**Submit**")

    data_to_submit = convert_df(labeled_data)
    # If the user clicks the "Submit" button
    if st.button("Submit"):
        s3_bucket_name = 'streamlit-posts-labeling'
        s3_data_path = 'labeled/labeled.csv'

        if upload_data_to_s3(data_to_submit, s3_bucket_name, s3_data_path):
            st.success(f"Data submitted and uploaded to S3: s3://{s3_bucket_name}/{s3_data_path}")
        else:
            st.error("Failed to upload the data to S3.")

    st.write("Labeled Data:")
    st.write(labeled_data)

if __name__ == "__main__":
    main()
