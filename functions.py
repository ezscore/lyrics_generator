import config
import requests
from bs4 import BeautifulSoup
from wordcloud import WordCloud

def lyr_to_df(dic, name): #lyrics to dataframe
    titles = []
    lyrics = []
    df = pd.DataFrame()
    for item in dic:
        for k,v in item.items():
            titles.append(k)
            lyrics.append(v)
    df['artist'] = [name] * len(titles)
    df['titles'] = titles
    df['lyrics'] = lyrics

    return df

def get_json(path, params=None, headers=None):
    '''Send request and get response in json format.'''
    base = "https://api.genius.com"
    # Generate request URL
    requrl = '/'.join([base, path])
    token = "Bearer {}".format(config.api_key)
    if headers:
        headers['Authorization'] = token
    else:
        headers = {"Authorization": token}

    # Get response object from querying genius api
    response = requests.get(url=requrl, params=params, headers=headers)
    response.raise_for_status()
    return response.json()

#function to get artist_id
def request_artist(artist_name):
    base_url = 'https://api.genius.com'
    headers = {'Authorization': 'Bearer ' + config.api_key}
    search_url = base_url + '/search'
    data = {'q':artist_name}
    response = requests.get(search_url, data=data, headers=headers)

    return response

#artist_id
def get_artist_id(response):
    artist_id = response.json()['response']['hits'][0]['result']['primary_artist']['id']
    return artist_id

#function to get song_id
def get_song_id(artist_id):
    '''Get all the song id from an artist.'''
    current_page = 1
    next_page = True
    songs = [] # to store final song ids
    titles = [] #to store final song titles

    while next_page:
        path = "artists/{}/songs/".format(artist_id)
        params = {'page': current_page} # the current page
        data = get_json(path=path, params=params) # get json of songs

        page_songs = data['response']['songs']
        if page_songs:
            # Add all the songs of current page
            songs += page_songs
            # Increment current_page value for next loop
            current_page += 1
            print("Page {} finished scraping".format(current_page))
            # If you don't wanna wait too long to scrape, un-comment this
            # if current_page == 2:
            #     break

        else:
            # If page_songs is empty, quit
            print('Collected lyrics for all songs')
            next_page = False
    return songs

#getting path to lyrics
def connect_lyrics(song_id):
    '''Constructs the path of song lyrics.'''
    url = "songs/{}".format(song_id)
    data = get_json(url)
    # Gets the path of song lyrics
    path = data['response']['song']['path']
    return path

#scrape song name + lyrics from path returns dictionary
def retrieve_lyrics(song_id):
    '''Retrieves lyrics from html page.'''
    s_dict = {}
    path = connect_lyrics(song_id)
    URL = "http://genius.com" + path
    page = requests.get(URL)

    # Extract the page's HTML as a string
    html = BeautifulSoup(page.text, "html.parser")

    # Scrape the song lyrics from the HTML
    lyrics = html.find("div", class_="lyrics").get_text()
    title = html.find('h1',class_='header_with_cover_art-primary_info-title').get_text()

    s_dict[title] = lyrics
    return s_dict

#RUN FUNCTION (MASTER) retrieve lyrics for artist and enter all lyrics and titles to dataframe
def productionize(name):
    song_lyrics = []

    artist = functions.request_artist(name)
    artist_id = functions.get_artist_id(artist)
    songs = functions.get_song_id(artist_id)

    songs = [song["id"] for song in songs
        if song["primary_artist"]["id"] == artist_id]

    for song in songs:
        song_lyrics.append(functions.retrieve_lyrics(song))

    print('Colleted all lyrics for {}'.format(name))
    return functions.lyr_to_df(song_lyrics, name)

#-----------------NLP FUNCTIONS-------------------#

#function that adds stopwords and tokenizes lyrics
def clean_tokenize_lyrics(song):
    stopwords_list = stopwords.words('english')
    stopwords_list += ["''", '""', '...', '``']
    stopwords_list += ['got', 'na', 'like', 'oh', 'ca', 'cause',\
                       'cause', 'want', 'ai', 'ya', 'yeah', 'let',\
                      'wanna', 'gotta', 'kinda', 'say', 'no', 'see',\
                      'que', 'la', 'gon', 'go', 'got', 'wan', 'uh', 'huh']
    word_list = []
    tokenized_lyrics = word_tokenize(song)
     #remove all tokens that are not alphabetic and stopwords
    words = [word for word in tokenized_lyrics if word not in stopwords_list and word.isalpha()]
    for word in words:
        word_list.append(word)
    return word_list

def word_cloud(words, name):
    wc = WordCloud(max_words=25, max_font_size=50).generate(words)
    plt.figure(figsize=(20,20))
    plt.title('WordCloud of most used words for {}'.format(name),fontsize=45)
    plt.imshow(wc, interpolation='bilinear')
    plt.axis("off")
    plt.show()
