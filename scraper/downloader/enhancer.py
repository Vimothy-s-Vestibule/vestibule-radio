import time
import queue
import threading
import logging
import requests
import os
import re
import json
import musicbrainzngs
from dotenv import load_dotenv
from concurrent.futures import Future
from difflib import SequenceMatcher
from pathlib import Path
from downloader.dl_types import TrackMetadata

#logger = logging.getLogger(__name__)

_RATE_INTERVAL_MB = 1.05
_RATE_INTERVAL_LF = 0.21
_CIRCUIT_COOLDOWN = 30  # seconds before retrying after service error


class Enhancer:
    """
    Get Track-Metadata from LastFM and MusicBrainz
    """
    def __init__(self):
        # TODO: change this useragent (esp. version and contact info)
        musicbrainzngs.set_useragent("vestibule-radio", "0.2", "pixl.808 on discord")
        self._queue: queue.Queue[tuple[TrackMetadata, Future]] = queue.Queue()

        load_dotenv()
        self.lastfm_api_key = os.getenv("LAST_FM_API_KEY")
        
        self.genre_list = set(json.loads((Path(__file__).parent / "genres.json").read_text()))
        self.genre_list_normalized = {self._normalize(g): g for g in self.genre_list}

        self._last_request_mb = 0.0
        self._last_request_lf = 0.0
        self._circuit_open_until = 0.0
        self._worker = threading.Thread(target=self._run, daemon=True)
        self._worker.start()
        
    def _run(self):
        while True:
            data, future = self._queue.get()

            if time.monotonic() < self._circuit_open_until:
                future.set_result(data)
                continue

            try:
                future.set_result(self._query_and_merge(data))
            except musicbrainzngs.WebServiceError as e:
                #logger.warning("MusicBrainz unavailable, opening circuit for %ds: %s", _CIRCUIT_COOLDOWN, e)
                self._circuit_open_until = time.monotonic() + _CIRCUIT_COOLDOWN
                future.set_result(data)
            except Exception as e:
                #logger.warning("Lookup failed for '%s': %s", data.title, e)
                future.set_result(data)
        
    def get_enhanced_data(self, data: TrackMetadata) -> TrackMetadata:
        future: Future[TrackMetadata] = Future()
        self._queue.put((data, future))
        return future.result()
    
    def _query_and_merge(self, data: TrackMetadata) -> TrackMetadata:
        # query lastfm first
        lastfm_data = self._get_metadata_from_lf(data)
        
        updates = {}
        updates["genres"] = lastfm_data.genres
        updates["album"] = lastfm_data.album
        updates["mbid"] = lastfm_data.mbid
        updates["artist"] = lastfm_data.artist

        # only query musicbrainz on stuff we didn't get from LastFM

        if lastfm_data.album == "" or lastfm_data.genres == []:
            result = self._mb_call(
                musicbrainzngs.search_recordings,
                recording=data.title,
                artist=data.artist,
                limit=5,
            )
            recordings = result.get("recording-list", [])
            if not recordings:
                return data.model_copy(update=updates)

            best, score = self._best_match(recordings, data.title, data.artist, data.duration_seconds)
            if (best is not None) and score >= 0.35:
                if lastfm_data.album == "":
                    releases = best.get("release-list", [])
                    if releases:
                        updates["album"] = releases[0]["title"]
                if lastfm_data.genres == []:
                    tags = self._get_mb_genre_tags(best)
                    if tags:
                        def tag_count(t): return int(t.get("count", 0))
                        valid = sorted(
                            [t for t in tags if self._is_valid_tag(t["name"])],
                            key=tag_count,
                            reverse=True,
                        )
                        if valid:
                            updates["genres"] = [t["name"] for t in valid[:5]]
        

        return data.model_copy(update=updates) if updates else data

    class MetaDataResult():
        mbid: str
        album: str
        artist: str
        genres: list [str]

    def _get_metadata_from_lf(self, trackMetaData: TrackMetadata) -> MetaDataResult:
        m = self.MetaDataResult()
        m.album = ""
        m.genres = []
        m.mbid = ""
        m.artist = trackMetaData.artist

        track = trackMetaData.title
        artist = trackMetaData.artist

        track = track.replace(' ', '+')
        artist = artist.replace(' ', '+')

        #1) query lastfm for matching track/artist + mbid
        url = f'http://ws.audioscrobbler.com/2.0/?method=track.search&track={track}&artist={artist}&api_key={self.lastfm_api_key}&format=json'
        response = self._lastfm_call(url)
        data = response.json()

        tracks = data['results']['trackmatches']['track']
        
        if len(tracks) == 0:
            return m
        
        artist = tracks[0]['artist']
        if artist:
            m.artist = artist
        track = tracks[0]['name'].replace(' ', '+')
        m.mbid = tracks[0]['mbid']
        
        #2) query lastfm for info (returns album + tags)
        url = f'http://ws.audioscrobbler.com/2.0/?method=track.getInfo&artist={artist}&track={track}&api_key={self.lastfm_api_key}&format=json'
        response = self._lastfm_call(url)
        data = response.json()
        
        if response.status_code == 200:
            try:     
                tags = data['track']['toptags']['tag']
                count = 0
                for i in range(len(tags)):
                    tag = tags[i]['name']
                    if self._is_valid_tag(tag):
                        m.genres.append(tag)
                        count += 1
                    if count >= 5:
                        break
            except:
                pass

            try:
                m.album = data['track']['album']['title']
            except:
                pass
            
        return m

    def _mb_call(self, func, *args, **kwargs):
        wait = _RATE_INTERVAL_MB - (time.monotonic() - self._last_request_mb)
        if wait > 0:
            time.sleep(wait)
        result = func(*args, **kwargs)
        self._last_request_mb = time.monotonic()
        return result
    
    def _lastfm_call(self, url):
        wait = _RATE_INTERVAL_LF - (time.monotonic() - self._last_request_lf)
        if wait > 0:
            time.sleep(wait)
        self._last_request_lf = time.monotonic()
        response = requests.get(url)
        return response

    def _normalize(self, s):
        return re.sub(r"[^a-z0-9]", "", s.lower())
    
    def _is_valid_tag(self, tag: str) -> bool:
        return self._normalize(tag.lower()) in self.genre_list_normalized
        
    def _similarity(self, a: str, b: str) -> float:
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()

    def _best_match(self, recordings: list, title: str, artist: str, duration_seconds: float):
        #Weighted average of 50% title string, 30% artist string, 20% duration match
        best, best_score = None, 0.0
        for rec in recordings:
            t = self._similarity(rec.get("title", ""), title)
            a = self._similarity(rec.get("artist-credit-phrase", ""), artist)
            d = 0.0
            if "length" in rec and duration_seconds:
                diff = abs(int(rec["length"]) / 1000 - duration_seconds)
                d = max(0.0, 1.0 - diff / 30)  # full score within a 30s window
            score = 0.5 * t + 0.3 * a + 0.2 * d
            if score > best_score:
                best_score, best = score, rec
        return best, best_score

    def _get_mb_genre_tags(self, recording: dict) -> list:
        releases = recording.get("release-list", [])
        if not releases:
            return []
        rg_id = releases[0].get("release-group", {}).get("id")
        if not rg_id:
            return []
        rg_data = self._mb_call(
            musicbrainzngs.get_release_group_by_id,
            rg_id,
            includes=["tags"],
        )
        return rg_data.get("release-group", {}).get("tag-list", [])

