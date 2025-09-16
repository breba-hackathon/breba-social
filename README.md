Breba Social is a revolution in social media.
Instead of having opaque algorithms control what you see, you control it.

Your personal agents will filter, curate and present your feed in a unique to you way.


# How it works
The project works by listening to bsky social posts.

```shell
python bsky_stream.py
```

Then you need to start the app that is hardcoded to listen to given social media personalities.
```shell
python app.py
```

Now you are ready to view your feed located inside breba_social/agents/pages/feed.html.

Whenever one of the social media personalities in the list of personalities we are subscribed to makes a post, our social media feed will be updated.


