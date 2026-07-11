const API = '';

const STATES = {
idle: { tag: 'Idle', text: 'Press play to tune in' },
connecting: { tag: 'Connecting', text: 'Tuning in' },
buffering: { tag: 'Buffering', text: 'Catching the signal' },
playing: { tag: 'Live', text: 'On air' },
paused: { tag: 'Paused', text: 'Paused' },
error: { tag: 'Off air', text: 'Nothing in the queue' },
};

// simple padding helper
function padLeft(value, width) {
width = width || 2;

let str = String(value);

while (str.length < width) {
    str = '0' + str;
}

return str;

}

// convert ms into HH:MM:SS
function formatSessionTime(ms) {
let seconds = Math.floor(ms / 1000);

if (seconds < 0) {
    seconds = 0; // is this a meme?
}

let hours = Math.floor(seconds / 3600);
let minutes = Math.floor(seconds / 60) % 60;
let secs = seconds % 60;

return padLeft(hours) + ':' + padLeft(minutes) + ':' + padLeft(secs);

}

// the api gives us seconds, the ticker wants MM:SS
function formatTrackTime(seconds) {
let mins = Math.floor(seconds / 60);
let secs = Math.floor(seconds % 60);

return mins + ':' + padLeft(secs);

}

// youtube loads its api script once, globally, and calls this when it's ready.
// anything that needs YT.Player has to wait on this promise.
let apiReady = null;

function loadYouTubeAPI() {
if (apiReady) {
    return apiReady;
}

apiReady = new Promise(function (resolve) {
    window.onYouTubeIframeAPIReady = resolve;

    let script = document.createElement('script');
    script.src = 'https://www.youtube.com/iframe_api';
    document.head.appendChild(script);
});

return apiReady;

}

class StreamPlayer {

constructor(rootEl) {
    this.root = rootEl;

    // collect references
    this.refs = {};

    let scopes = [rootEl].concat(
        Array.from(document.querySelectorAll('[data-player-panel]'))
    );

    for (let s = 0; s < scopes.length; s++) {
        let nodes = scopes[s].querySelectorAll('[data-ref]');

        for (let i = 0; i < nodes.length; i++) {
            let key = nodes[i].dataset.ref;
            this.refs[key] = nodes[i];
        }
    }

    this.actions = {
        toggle: this.toggle,
        stop: this.stop,
        mute: this.mute,
        next: this.next
    };

    this.timer = null;
    this.startedAt = 0;
    this.elapsed = 0;

    this.playing = false;
    this.muted = false;
    this.volume = 80;

    this.yt = null;
    this.queue = [];
    this.index = 0;

    this.bindEvents();

    // initialize volume (quietly)
    if (this.refs.volume) {
        this.setVolume(this.refs.volume.valueAsNumber, { silent: true });
    }

    this.setState('idle');

    this.loadQueue();
}


async loadQueue() {
    try {
        let res = await fetch(API + '/queue');

        if (!res.ok) {
            throw new Error('queue responded ' + res.status);
        }

        this.queue = await res.json();
    } catch (e) {
        console.warn('Could not load the queue', e);
        this.queue = [];
    }

    this.renderQueue();

    if (this.queue.length) {
        this.renderNowPlaying(this.queue[0]);
    } else {
        this.setState('error');
    }
}


bindEvents() {
    let self = this;

    // click handling
    this.root.addEventListener('click', function (e) {
        let el = e.target.closest('[data-action]');

        if (!el) return;

        let action = el.dataset.action;

        if (self.actions[action]) {
            self.actions[action].call(self);
        }
    });

    // volume change
    if (this.refs.volume) {
        this.refs.volume.addEventListener('input', function (e) {
            self.setVolume(e.target.valueAsNumber);
        });
    }


    this.root.addEventListener('keydown', function (e) {
        if (e.target.matches('input, button, [contenteditable]')) {
            return;
        }

        if (e.code === 'Space') {
            e.preventDefault();
            self.toggle();
        }
    });
}


// build the embed on first play. youtube won't autoplay with sound before a
// user gesture anyway, so there's no reason to mount it any earlier.
async createPlayer() {
    await loadYouTubeAPI();

    let self = this;

    return new Promise(function (resolve) {
        self.yt = new YT.Player(self.refs.mount, {
            videoId: self.current().video_id,
            playerVars: {
                autoplay: 1,
                controls: 0,
                disablekb: 1,
                modestbranding: 1,
                rel: 0,
                playsinline: 1
            },
            events: {
                onReady: function (e) {
                    e.target.setVolume(self.volume);

                    if (self.muted) {
                        e.target.mute();
                    }

                    resolve();
                },
                onStateChange: function (e) {
                    self.onYTState(e.data);
                },
                onError: function () {
                    // a dead or region-locked video shouldn't stall the station
                    self.next();
                }
            }
        });
    });
}


onYTState(code) {
    if (code === YT.PlayerState.PLAYING) {
        this.setState('playing');
    } else if (code === YT.PlayerState.BUFFERING) {
        this.setState('buffering');
    } else if (code === YT.PlayerState.PAUSED) {
        this.setState('paused');
    } else if (code === YT.PlayerState.ENDED) {
        this.next();
    }
}


current() {
    return this.queue[this.index] || null;
}


async toggle() {
    if (!this.queue.length) {
        this.setState('error');
        return;
    }

    if (this.yt) {
        if (this.playing) {
            this.yt.pauseVideo();
        } else {
            this.yt.playVideo();
        }
        return;
    }

    this.setState('connecting');
    this.showEmbed();

    await this.createPlayer();
}


next() {
    if (!this.queue.length) return;

    this.index = (this.index + 1) % this.queue.length;

    let track = this.current();

    this.stopTimer();

    this.renderNowPlaying(track);
    this.renderQueue();

    if (this.yt) {
        this.yt.loadVideoById(track.video_id);
    }
}


stop() {
    if (this.yt) {
        this.yt.stopVideo();
    }

    this.setState('idle');
}


mute() {
    this.muted = !this.muted;

    if (this.yt) {
        if (this.muted) {
            this.yt.mute();
        } else {
            this.yt.unMute();
        }
    }

    this.renderMuteButton();
}


setVolume(value, options) {
    options = options || {};

    let silent = options.silent === true;

    this.volume = value;

    if (this.yt) {
        this.yt.setVolume(value);
    }

    if (this.refs.volumeReadout) {
        this.refs.volumeReadout.textContent = padLeft(value, 3);
    }

    // auto-unmute if needed
    if (!silent && this.muted && value > 0) {
        this.mute();
    }
}


// swap the lyre for the real player. youtube's terms want the video visible :/
showEmbed() {
    if (this.refs.poster) {
        this.refs.poster.classList.add('hidden');
    }

    if (this.refs.embed) {
        this.refs.embed.classList.remove('hidden');
    }
}


setState(name) {
    let state = STATES[name];

    if (!state) {
        console.warn('Invalid state:', name);
        return;
    }

    this.root.dataset.state = name;

    if (this.refs.stateTag) {
        this.refs.stateTag.textContent = state.tag;
    }

    if (this.refs.stateText) {
        this.refs.stateText.textContent = state.text;
    }

    this.playing = name === 'playing';

    this.renderPlayButton(this.playing);

    // buffering shouldn't wipe the clock, only stopping should
    if (this.playing) {
        this.startTimer();
    } else if (name === 'idle' || name === 'error') {
        this.stopTimer();
    } else {
        this.pauseTimer();
    }
}


renderNowPlaying(track) {
    if (!track) return;

    if (this.refs.npTitle) {
        this.refs.npTitle.textContent = track.title || 'Unknown track';
    }

    if (this.refs.npArtist) {
        this.refs.npArtist.textContent = track.artist || '';
    }

    if (this.refs.npBy) {
        this.refs.npBy.textContent = track.posted_by ? 'Posted by ' + track.posted_by : '';
    }

    if (this.refs.npThumb) {
        this.refs.npThumb.src = 'https://i.ytimg.com/vi/' + track.video_id + '/mqdefault.jpg';
        this.refs.npThumb.alt = track.title || '';
        this.refs.npThumb.classList.remove('hidden');
    }
}


renderQueue() {
    let list = this.refs.queue;

    if (!list) return;

    list.textContent = '';

    if (!this.queue.length) {
        let li = document.createElement('li');
        li.className = 'border-b border-ink/15 py-2 opacity-60';
        li.textContent = 'Nothing queued. Go post a link.';
        list.appendChild(li);
        return;
    }

    // everything after the current track, wrapping back around
    for (let i = 1; i < this.queue.length; i++) {
        let track = this.queue[(this.index + i) % this.queue.length];

        let li = document.createElement('li');
        li.className = 'flex justify-between gap-4 border-b border-ink/15 py-2';

        let name = document.createElement('span');
        name.textContent = [track.artist, track.title].filter(Boolean).join(' — ') || 'Unknown track';

        let time = document.createElement('span');
        time.className = 'shrink-0 tabular-nums opacity-60';
        time.textContent = track.duration_seconds ? formatTrackTime(track.duration_seconds) : '';

        li.appendChild(name);
        li.appendChild(time);
        list.appendChild(li);
    }
}


renderPlayButton(isPlaying) {
    let btn = this.refs.playBtn;
    if (!btn) return;

    btn.setAttribute('aria-pressed', isPlaying ? 'true' : 'false');
    btn.setAttribute('aria-label', isPlaying ? 'Pause' : 'Play');
}


renderMuteButton() {
    let btn = this.refs.muteBtn;
    if (!btn) return;

    let muted = this.muted;

    btn.setAttribute('aria-pressed', muted ? 'true' : 'false');
    btn.textContent = muted ? 'Unmute' : 'Mute';
}


startTimer() {
    if (this.timer) {
        return; // already running
    }

    this.startedAt = performance.now();

    let self = this;

    this.timer = setInterval(function () {
        let elapsed = self.elapsed + (performance.now() - self.startedAt);

        if (self.refs.elapsed) {
            self.refs.elapsed.textContent = formatSessionTime(elapsed);
        }

    }, 1000);
}


// bank the time so far, so a buffer stall or a pause doesn't lose it
pauseTimer() {
    if (!this.timer) return;

    clearInterval(this.timer);
    this.timer = null;

    this.elapsed += performance.now() - this.startedAt;
}


stopTimer() {
    if (this.timer) {
        clearInterval(this.timer);
        this.timer = null;
    }

    this.elapsed = 0;

    if (this.refs.elapsed) {
        this.refs.elapsed.textContent = '00:00:00';
    }
}

}

// init
let players = document.querySelectorAll('[data-component="stream-player"]');

for (let i = 0; i < players.length; i++) {
new StreamPlayer(players[i]);
}