(() => {
    const $ = (sel) => document.querySelector(sel);
    const form = $('#promptForm');
    const outputSection = $('#outputSection');
    const promptOutput = $('#promptOutput');
    const negativeOutput = $('#negativeOutput');
    const negativeText = $('#negativeText');
    const historyList = $('#historyList');

    const STYLE_MAP = {
        'cinematic': 'cinematic film style, anamorphic lens, shallow depth of field',
        'photorealistic': 'photorealistic, ultra-realistic, 8K resolution',
        'anime': 'anime style, cel-shaded, vibrant animation',
        '3d-render': '3D rendered, CGI, Unreal Engine quality',
        'watercolor': 'watercolor painting style, soft flowing textures',
        'oil-painting': 'oil painting style, rich brushstrokes, textured canvas',
        'pixel-art': 'pixel art style, retro 16-bit aesthetic',
        'noir': 'film noir style, high contrast black and white, dramatic shadows',
        'cyberpunk': 'cyberpunk aesthetic, neon-lit, futuristic dystopia',
        'fantasy': 'epic fantasy style, dramatic and grand, painterly',
        'documentary': 'documentary style, raw footage, naturalistic',
        'stop-motion': 'stop-motion animation style, tactile, handcrafted look',
        'vaporwave': 'vaporwave aesthetic, retro-futuristic, glitch art',
        'minimalist': 'minimalist style, clean lines, simple composition',
    };

    const MOOD_MAP = {
        'epic': 'epic and grandiose atmosphere',
        'serene': 'serene and peaceful atmosphere',
        'mysterious': 'mysterious and enigmatic atmosphere',
        'dark': 'dark and ominous atmosphere',
        'joyful': 'joyful and uplifting atmosphere',
        'melancholic': 'melancholic and reflective atmosphere',
        'tense': 'tense and suspenseful atmosphere',
        'dreamy': 'dreamy and ethereal atmosphere',
        'nostalgic': 'nostalgic and warm atmosphere',
        'chaotic': 'chaotic and high-energy atmosphere',
    };

    const CAMERA_MAP = {
        'slow-pan': 'slow cinematic pan',
        'tracking-shot': 'smooth tracking shot following the subject',
        'drone-aerial': 'sweeping drone aerial shot',
        'dolly-zoom': 'dramatic dolly zoom (vertigo effect)',
        'handheld': 'handheld camera with natural shake',
        'static': 'locked-off static camera',
        'orbit': 'orbiting 360-degree camera movement',
        'crane': 'crane shot rising upward',
        'first-person': 'first-person POV shot',
        'timelapse': 'timelapse photography',
        'slow-motion': 'slow motion capture',
        'zoom-in': 'gradual zoom in on the subject',
        'zoom-out': 'slow zoom out revealing the scene',
    };

    const SHOT_MAP = {
        'wide': 'wide establishing shot',
        'medium': 'medium shot',
        'close-up': 'close-up shot',
        'extreme-close-up': 'extreme close-up, macro detail',
        'over-the-shoulder': 'over-the-shoulder shot',
        'birds-eye': "bird's eye view from directly above",
        'low-angle': 'low angle shot looking upward',
        'high-angle': 'high angle shot looking downward',
        'dutch-angle': 'tilted dutch angle for unease',
    };

    const LIGHTING_MAP = {
        'golden-hour': 'warm golden hour sunlight',
        'blue-hour': 'cool blue hour twilight',
        'neon': 'vibrant neon RGB lighting',
        'natural': 'natural daylight',
        'studio': 'professional studio lighting',
        'moonlight': 'soft moonlight illumination',
        'silhouette': 'dramatic backlit silhouette',
        'volumetric': 'volumetric light rays, god rays',
        'candlelight': 'warm flickering candlelight',
        'overcast': 'soft overcast diffused light',
        'dramatic': 'dramatic chiaroscuro lighting',
    };

    const COLOR_MAP = {
        'warm': 'warm color palette with amber, gold, and red tones',
        'cool': 'cool color palette with blue, teal, and silver tones',
        'muted': 'muted desaturated colors',
        'vibrant': 'vibrant saturated colors',
        'monochrome': 'monochrome color scheme',
        'pastel': 'soft pastel color palette',
        'neon-palette': 'electric neon color palette',
        'earthy': 'natural earthy tones',
        'high-contrast': 'high contrast color grading',
    };

    const TOOL_HINTS = {
        'sora': 'Optimized for Sora: ',
        'runway': 'Optimized for Runway Gen-3: ',
        'pika': 'Optimized for Pika: ',
        'kling': 'Optimized for Kling AI: ',
        'minimax': 'Optimized for MiniMax/Hailuo: ',
        'stable-video': 'Optimized for Stable Video Diffusion: ',
        'veo': 'Optimized for Google Veo: ',
    };

    let history = JSON.parse(localStorage.getItem('vpg-history') || '[]');

    function buildPrompt() {
        const subject = $('#subject').value.trim();
        if (!subject) return null;

        const style = $('#style').value;
        const mood = $('#mood').value;
        const camera = $('#camera').value;
        const shot = $('#shot').value;
        const lighting = $('#lighting').value;
        const setting = $('#setting').value.trim();
        const colors = $('#colors').value;
        const duration = $('#duration').value;
        const ratio = $('#ratio').value;
        const tool = $('#tool').value;
        const details = $('#details').value.trim();
        const negative = $('#negative').value.trim();

        const parts = [];

        // Tool prefix
        if (tool && TOOL_HINTS[tool]) {
            parts.push(TOOL_HINTS[tool]);
        }

        // Core subject
        parts.push(subject);

        // Style
        if (style && STYLE_MAP[style]) {
            parts.push(STYLE_MAP[style]);
        }

        // Shot type
        if (shot && SHOT_MAP[shot]) {
            parts.push(SHOT_MAP[shot]);
        }

        // Camera
        if (camera && CAMERA_MAP[camera]) {
            parts.push(CAMERA_MAP[camera]);
        }

        // Lighting
        if (lighting && LIGHTING_MAP[lighting]) {
            parts.push(LIGHTING_MAP[lighting]);
        }

        // Mood
        if (mood && MOOD_MAP[mood]) {
            parts.push(MOOD_MAP[mood]);
        }

        // Setting
        if (setting) {
            parts.push(`set in ${setting}`);
        }

        // Colors
        if (colors && COLOR_MAP[colors]) {
            parts.push(COLOR_MAP[colors]);
        }

        // Details
        if (details) {
            parts.push(details);
        }

        // Technical specs
        const specs = [];
        if (duration) specs.push(duration + ' duration');
        if (ratio) specs.push(ratio + ' aspect ratio');
        if (specs.length) {
            parts.push(specs.join(', '));
        }

        return {
            prompt: parts.join('. ').replace(/\.\./g, '.').replace(/\. :/g, ':'),
            negative: negative || null,
        };
    }

    function renderHistory() {
        if (history.length === 0) {
            historyList.innerHTML = '<p style="color:var(--text-muted);font-size:0.9rem;">No prompts generated yet.</p>';
            return;
        }
        historyList.innerHTML = history.map((item, i) => `
            <div class="history-item" data-index="${i}">
                <div class="history-preview">${escapeHtml(item.prompt)}</div>
                <span class="history-time">${item.time}</span>
            </div>
        `).join('');
    }

    function escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    function showToast(msg) {
        let toast = $('.toast');
        if (!toast) {
            toast = document.createElement('div');
            toast.className = 'toast';
            document.body.appendChild(toast);
        }
        toast.textContent = msg;
        toast.classList.add('show');
        setTimeout(() => toast.classList.remove('show'), 2000);
    }

    async function copyText(text, btn) {
        try {
            await navigator.clipboard.writeText(text);
            btn.classList.add('copied');
            btn.innerHTML = '<span class="copy-icon">&#10003;</span> Copied!';
            showToast('Copied to clipboard');
            setTimeout(() => {
                btn.classList.remove('copied');
                btn.innerHTML = '<span class="copy-icon">&#128203;</span> Copy';
            }, 2000);
        } catch {
            showToast('Failed to copy');
        }
    }

    function randomize() {
        const subjects = [
            'A dragon soaring over a medieval castle at sunset',
            'A cybernetic wolf running through a neon-lit city',
            'An astronaut floating in space with Earth in the background',
            'A samurai meditating under cherry blossoms in the rain',
            'A deep sea creature glowing in the abyss',
            'A time traveler stepping through a shimmering portal',
            'A giant robot emerging from the ocean during a storm',
            'A fox walking through an enchanted glowing forest',
            'A vintage car driving down an endless desert highway',
            'A ballerina dancing on a frozen lake under the aurora borealis',
            'A steampunk airship sailing through thunderclouds',
            'A lone figure walking through an abandoned neon arcade',
        ];

        function randomOption(select) {
            const options = select.querySelectorAll('option');
            const nonEmpty = Array.from(options).filter(o => o.value);
            if (nonEmpty.length) {
                const pick = nonEmpty[Math.floor(Math.random() * nonEmpty.length)];
                select.value = pick.value;
            }
        }

        $('#subject').value = subjects[Math.floor(Math.random() * subjects.length)];
        randomOption($('#style'));
        randomOption($('#mood'));
        randomOption($('#camera'));
        randomOption($('#shot'));
        randomOption($('#lighting'));
        randomOption($('#colors'));
        randomOption($('#duration'));
        randomOption($('#ratio'));

        $('#setting').value = '';
        $('#details').value = '';
        $('#negative').value = '';
    }

    // Event listeners
    form.addEventListener('submit', (e) => {
        e.preventDefault();
        const result = buildPrompt();
        if (!result) {
            showToast('Please enter a subject');
            return;
        }

        promptOutput.textContent = result.prompt;
        outputSection.classList.remove('hidden');

        if (result.negative) {
            negativeText.textContent = result.negative;
            negativeOutput.style.display = 'block';
        } else {
            negativeOutput.style.display = 'none';
        }

        // Save to history
        const now = new Date();
        const time = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        history.unshift({ prompt: result.prompt, negative: result.negative, time });
        if (history.length > 20) history.pop();
        localStorage.setItem('vpg-history', JSON.stringify(history));
        renderHistory();

        outputSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });

    $('#copyBtn').addEventListener('click', () => {
        copyText(promptOutput.textContent, $('#copyBtn'));
    });

    $('#copyNegBtn').addEventListener('click', () => {
        copyText(negativeText.textContent, $('#copyNegBtn'));
    });

    $('#randomBtn').addEventListener('click', randomize);

    $('#clearBtn').addEventListener('click', () => {
        outputSection.classList.add('hidden');
    });

    $('#clearHistoryBtn').addEventListener('click', () => {
        history = [];
        localStorage.removeItem('vpg-history');
        renderHistory();
        showToast('History cleared');
    });

    historyList.addEventListener('click', (e) => {
        const item = e.target.closest('.history-item');
        if (!item) return;
        const idx = parseInt(item.dataset.index);
        const entry = history[idx];
        if (!entry) return;

        promptOutput.textContent = entry.prompt;
        outputSection.classList.remove('hidden');

        if (entry.negative) {
            negativeText.textContent = entry.negative;
            negativeOutput.style.display = 'block';
        } else {
            negativeOutput.style.display = 'none';
        }

        outputSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });

    // Init
    renderHistory();
})();
