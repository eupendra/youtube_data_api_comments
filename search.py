import json
import logging
import googleapiclient.discovery

logger = logging.getLogger(__name__)
FORMAT = "[%(filename)s:%(lineno)s:%(funcName)s()] %(message)s"
logging.basicConfig(format=FORMAT)
logger.setLevel(logging.DEBUG)


def build_youtube(API_KEY):
    api_service_name = "youtube"
    api_version = "v3"
    youtube = googleapiclient.discovery.build(
        api_service_name, api_version, developerKey=API_KEY)
    return youtube


def search_videos(youtube, channel_id, page_token):
    request = youtube.search().list(
        part="snippet",
        channelId=channel_id,
        type="video",
        pageToken=page_token
    )
    response = request.execute()
    logger.debug("Received Video Search Response")
    return response


def search_comments(youtube, video_id, page_token):
    request = youtube.commentThreads().list(
        part="snippet",
        videoId=video_id,
        pageToken=page_token
    )
    logger.debug(f"Received comment Search Response for {video_id} ")

    response = request.execute()
    return response


def process_search_response(response):
    next_page_token = response.get('nextPageToken')
    result = []
    for i, item in enumerate(response["items"]):
        video_id = item["id"]["videoId"]
        video_title = item['snippet']['title']
        result.append({
            'video_id': video_id,
            'video_title': video_title
        })
        logger.debug(f"Received comment Search Response for {video_id} ")

    return next_page_token, result


def process_comments_response(response, video):
    next_page_token = response.get('nextPageToken')
    result = []
    for i, item in enumerate(response["items"]):
        comment = item["snippet"]["topLevelComment"]
        author = comment["snippet"]["authorDisplayName"]  # Use Later
        comment_text = comment["snippet"]["textDisplay"]
        video_id = video['video_id']
        video_title = video['video_title']
        result.append(
            {
                'video_id': video_id,
                'video_title': video_title,
                'author': author,
                'comment_text': comment_text
            }
        )
        logger.debug(f"Comment: {comment_text[:50]}... for {video_title}")

    return next_page_token, result


def main():
    # READING API and CHANNEL ID from config.json

    config_file_name = "config.json"
    with open(config_file_name) as config_file:
        config = json.load(config_file)
    api_key = config["API_KEY"]
    channel_id = config["CHANNEL_ID"]

    youtube = build_youtube(api_key)

    videos = []
    comments = []
    try:
        next_page = None
        while True:
            response = search_videos(youtube, channel_id, next_page)
            next_page, result = process_search_response(response)
            videos += result
            if not next_page:
                break

        for video in videos:
            next_page = None
            while True:
                response = search_comments(youtube, video['video_id'], next_page)
                next_page, result = process_comments_response(response, video)
                comments += result
                if not next_page:
                    break
    except Exception as e:
        logger.error(f"Error:\n{str(e)}")
    print(f"Total comments: {len(comments)}")
    print(f"Total videos: {len(videos)}")
    
    with open('all_comments.json', 'w', encoding='utf-8') as f:
        json.dump(comments, f, indent=4)


if __name__ == "__main__":
    main()
