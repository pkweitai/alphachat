
document.addEventListener('DOMContentLoaded', function() {
    const widgetsContainer = document.getElementById('widgets-container');
    const newsDetail = document.getElementById('news-detail');
    const videoPlayer = document.getElementById('video-player');
    const searchBox = document.getElementById('search-box');
    const searchButton = document.getElementById('search-button');
    const generateScriptCheckbox = document.getElementById('generate-script-checkbox');
    const limit = 5;
    let allNewsItems = [];
    let currentStartIndex = 0;
    let currentWidgetIndex = 0;
    let youtubeVideos = [];
    let currentVideoIndex = 0;


    function extractDate(dateStr) {
        const dateMatch = dateStr.match(/<p>(.*?)<\/p>/);
        return dateMatch ? dateMatch[1] : 'now';
    }
    
    function timeAgo(dateStr) {
        const date = new Date(dateStr);
        const now = new Date();
        const diffInSeconds = Math.floor((now - date) / 1000);
        const diffInMinutes = Math.floor(diffInSeconds / 60);
        const diffInHours = Math.floor(diffInMinutes / 60);
        const diffInDays = Math.floor(diffInHours / 24);
        const diffInMonths = Math.floor(diffInDays / 30);
        const diffInYears = Math.floor(diffInDays / 365);
    
        if (diffInSeconds < 60) {
            return 'now';
        } else if (diffInMinutes < 60) {
            return `${diffInMinutes} minutes ago`;
        } else if (diffInHours < 24) {
            return `${diffInHours} hours ago`;
        } else if (diffInDays < 30) {
            return `${diffInDays} days ago`;
        } else if (diffInMonths < 12) {
            return `${diffInMonths} months ago`;
        } else {
            return `${diffInYears} years ago`;
        }
    }
    
    function updateWidgets() {
        widgetsContainer.innerHTML = '';
        const endIndex = Math.min(currentStartIndex + limit, allNewsItems.length);
        const widgets = allNewsItems.slice(currentStartIndex, endIndex);

        widgets.forEach((newsItem, index) => {
            const widget = document.createElement('div');
            const system="reference to story below, summarize and  build the following content in 3 scenes and with 1 image each scene, start at 1% : \n";
            widget.classList.add('news-widget');
            const imageUrl = newsItem[6];
            const dateText = extractDate(newsItem[5]);
            const timeElapsed = dateText !== 'now' ? timeAgo(dateText) : 'now';
                
            widget.innerHTML = `
                <div class="news-widget-content">
                    <img class="news-widget-image" src="${imageUrl}" alt="News Image" onerror="this.onerror=null;this.src='${defaultImageUrl}';">
                    <h3>${newsItem[0]}</h3>
                <p>${timeElapsed}  ${newsItem[4].split(' ').slice(0, 15).join(' ')}...</p>

                </div>
            `;
            widget.addEventListener('click', () => {
                newsDetail.innerHTML = `
                    <h2>${newsItem[0]}</h2>
                    <p>${newsItem[4]}</p>
                `;
                if (generateScriptCheckbox.checked) {
                    fetch('http://storyflix.live:5000/senddraft', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({ topic: newsItem[0], user: system+newsItem[4] })
                    }).then(response => {
                        if (!response.ok) {
                            console.error('Failed to send data to remote endpoint');
                        }
                    }).catch(error => {
                        console.error('Error:', error);
                    });
                }
            });


            widgetsContainer.appendChild(widget);

            if (currentStartIndex + index === currentWidgetIndex) {
                widget.classList.add('highlight');
            } else {
                widget.classList.remove('highlight');
            }
        });
    }

    function fetchNews(offset, append = false) {
        fetch(`/news?limit=${limit}&offset=${offset}`)
            .then(response => response.json())
            .then(news => {
                if (append) {
                    allNewsItems = allNewsItems.concat(news);
                } else {
                    allNewsItems = news;
                }
                updateWidgets();
            });
    }

    function fetchYouTubeVideos() {
        fetch('/get_videos')
            .then(response => response.json())
            .then(videos => {
                youtubeVideos = videos;
                if (youtubeVideos.length > 0) {
                    playNextVideo();
                }
            });
    }

    function playNextVideo() {
        if (youtubeVideos.length === 0) return;

        const video = youtubeVideos[currentVideoIndex];
        const videoUrl = `https://www.youtube.com/embed/${video.yt_id}?start=${video.timestamp}&autoplay=1&mute=1`; // Ensure autoplay
        videoPlayer.src = videoUrl;
        console.log(video.yt_id)
        console.log(currentVideoIndex)
        console.log(video.timestamp)
        console.log(videoUrl)
        console.log("totla:"+youtubeVideos.length)
        console.log(youtubeVideos);
        currentVideoIndex = (currentVideoIndex + 1) % youtubeVideos.length;
    }

    function navigateWidgets(direction) {
        const maxIndex = allNewsItems.length - 1;
        if (direction === 'prev' && currentWidgetIndex > 0) {
            currentWidgetIndex--;
            if (currentWidgetIndex < currentStartIndex) {
                currentStartIndex--;
            }
        } else if (direction === 'next' && currentWidgetIndex < maxIndex) {
            currentWidgetIndex++;
            if (currentWidgetIndex >= currentStartIndex + limit) {
                currentStartIndex++;
            }
        }
        updateWidgets();
    }

    function searchVideos(keyword) {
        fetch('/searchfragment', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: `keyword=${encodeURIComponent(keyword)}`
        })
            .then(response => response.json())
            .then(urls => {
                youtubeVideos = urls.map(url => {
                    const yt_id = url.split('v=')[1].split('&')[0];
                    const t_param = url.split('t=')[1];
                    const timestamp = t_param ? t_param.replace('s', '') : '0';
                    return { yt_id, timestamp };
                });
                if (youtubeVideos.length > 0) {
                    currentVideoIndex = 0;
                    playNextVideo();
                }
            });
    }
    /*
    searchButton.addEventListener('click', () => {
        const keyword = searchBox.value.trim();
        if (keyword) {
            searchVideos(keyword);
        }
    });*/

    document.getElementById('prev').addEventListener('click', () => {
        navigateWidgets('prev');
    });

    document.getElementById('next').addEventListener('click', () => {
        navigateWidgets('next');
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'ArrowLeft') {
            navigateWidgets('prev');
        } else if (event.key === 'ArrowRight') {
            navigateWidgets('next');
        }
    });


    


    fetchNews(currentStartIndex);
    setInterval(() => fetchNews(allNewsItems.length, true), 36000);

    //fetchYouTubeVideos();
    //setInterval(() => fetchYouTubeVideos(), 36000);
    searchVideos("crypto news");
    setInterval(searchVideos("crypto news,cnbc"),360000);  //refresh every hour  
    setInterval(playNextVideo, 60000);  // Change video every 60 seconds
});
