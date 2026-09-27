/* ==========================================================
   EduHub — Interactions & Animations
   ========================================================== */

// ============ PAGE LOAD FADE ============
document.addEventListener('DOMContentLoaded', () => {
  document.body.classList.add('page-loaded');
});

// ============ THEME MANAGEMENT ============
(function () {
  const THEMES = ['light', 'dark', 'neumorphic', 'contrast'];

  function applyTheme(theme, silent) {
    if (!THEMES.includes(theme)) theme = 'light';
    document.documentElement.setAttribute('data-theme', theme);
    document.documentElement.setAttribute(
      'data-bs-theme',
      (theme === 'dark' || theme === 'contrast') ? 'dark' : 'light'
    );
    localStorage.setItem('theme', theme);
    updateThemeIcons(theme);
    document.querySelectorAll('[data-theme-option]').forEach(el => {
      el.classList.toggle('active', el.dataset.themeOption === theme);
    });

    if (!silent) {
      // Flash effect on theme change
      const flash = document.createElement('div');
      flash.className = 'theme-flash';
      document.body.appendChild(flash);
      setTimeout(() => flash.remove(), 700);
    }
  }

  function updateThemeIcons(theme) {
    const iconMap = {
      light: 'bi bi-sun-fill',
      dark: 'bi bi-moon-stars-fill',
      neumorphic: 'bi bi-circle-half',
      contrast: 'bi bi-brightness-high-fill',
    };
    document.querySelectorAll('#theme-toggle i, .theme-toggle-icon').forEach(i => {
      i.className = iconMap[theme] || 'bi bi-sun-fill';
    });
  }

  applyTheme(localStorage.getItem('theme') || 'light', true);

  document.addEventListener('click', (e) => {
    const btn = e.target.closest('#theme-toggle');
    if (btn) {
      const current = document.documentElement.getAttribute('data-theme') || 'light';
      const idx = THEMES.indexOf(current);
      const next = THEMES[(idx + 1) % THEMES.length];
      applyTheme(next);
      const labels = {
        light: '☀️ Light mode',
        dark: '🌙 Dark mode',
        neumorphic: '🎨 Neumorphic mode',
        contrast: '⚡ High contrast',
      };
      showToast(labels[next] || next);
      return;
    }
    const option = e.target.closest('[data-theme-option]');
    if (option) {
      e.preventDefault();
      applyTheme(option.dataset.themeOption);
    }
  });

  function showToast(msg) {
    const container = document.getElementById('toast-container');
    if (!container) return;
    const el = document.createElement('div');
    el.className = 'alert alert-info shadow-sm border-0';
    el.innerHTML = msg;
    container.appendChild(el);
    setTimeout(() => {
      el.style.animation = 'slideOutRight .4s ease forwards';
      setTimeout(() => el.remove(), 400);
    }, 2200);
  }

  window.applyTheme = applyTheme;
})();

// ============ SIDEBAR TOGGLE ============
document.addEventListener('click', (e) => {
  const toggle = e.target.closest('#menuToggle');
  const sidebar = document.getElementById('sidebar');
  const backdrop = document.getElementById('sidebarBackdrop');
  if (toggle) {
    sidebar?.classList.toggle('open');
    backdrop?.classList.toggle('show');
  }
  if (e.target.closest('#sidebarBackdrop')) {
    sidebar?.classList.remove('open');
    backdrop?.classList.remove('show');
  }
});

// ============ RIPPLE ON BUTTONS ============
document.addEventListener('click', (e) => {
  const btn = e.target.closest('.btn, .btn-ripple, .qa-card, .icon-btn');
  if (!btn) return;
  const r = btn.getBoundingClientRect();
  const ripple = document.createElement('span');
  ripple.className = 'ripple';
  ripple.style.left = (e.clientX - r.left) + 'px';
  ripple.style.top = (e.clientY - r.top) + 'px';
  btn.appendChild(ripple);
  setTimeout(() => ripple.remove(), 700);
});

// ============ FORM SUBMIT LOADING ============
document.addEventListener('submit', (e) => {
  const form = e.target;
  if (form.dataset.noLoading === 'true') return;
  const submitBtn = form.querySelector('button[type="submit"]');
  if (submitBtn && !submitBtn.classList.contains('btn-loading')) {
    submitBtn.classList.add('btn-loading');
  }
});

// ============ 3D CARD TILT ============
(function () {
  function attachTilt() {
    document.querySelectorAll('.course-card, .stat-tile, .qa-card').forEach(card => {
      card.addEventListener('mousemove', (e) => {
        const r = card.getBoundingClientRect();
        const x = e.clientX - r.left, y = e.clientY - r.top;
        const cx = r.width / 2, cy = r.height / 2;
        const rotX = ((y - cy) / cy) * -3;
        const rotY = ((x - cx) / cx) * 3;
        card.style.transform =
          `translateY(-8px) perspective(1000px) rotateX(${rotX}deg) rotateY(${rotY}deg)`;
      });
      card.addEventListener('mouseleave', () => { card.style.transform = ''; });
    });
  }
  if (document.readyState !== 'loading') attachTilt();
  else document.addEventListener('DOMContentLoaded', attachTilt);
})();

// ============ SCROLL REVEAL ============
(function () {
  const io = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add('reveal-in');
        io.unobserve(e.target);
      }
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -60px 0px' });

  const attach = () =>
    document.querySelectorAll('.reveal, .stagger').forEach(el => io.observe(el));

  if (document.readyState !== 'loading') attach();
  else document.addEventListener('DOMContentLoaded', attach);
})();

// ============ ANIMATED COUNTERS ============
(function () {
  function animate(el) {
    const target = parseFloat(el.dataset.target);
    const suffix = el.dataset.suffix || '';
    const duration = 1600;
    const start = performance.now();
    function step(now) {
      const t = Math.min((now - start) / duration, 1);
      const eased = 1 - Math.pow(1 - t, 3);
      el.textContent = Math.floor(target * eased) + suffix;
      if (t < 1) requestAnimationFrame(step);
      else el.textContent = target + suffix;
    }
    requestAnimationFrame(step);
  }
  const io = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) { animate(e.target); io.unobserve(e.target); }
    });
  }, { threshold: 0.4 });

  const attach = () =>
    document.querySelectorAll('.counter').forEach(el => io.observe(el));

  if (document.readyState !== 'loading') attach();
  else document.addEventListener('DOMContentLoaded', attach);
})();

// ============ AUTO-DISMISS ALERTS ============
document.querySelectorAll('.alert-dismissible').forEach(el => {
  setTimeout(() => {
    if (el && el.parentNode) {
      el.style.animation = 'slideOutRight .4s ease forwards';
      setTimeout(() => {
        try { bootstrap.Alert.getOrCreateInstance(el).close(); } catch {}
      }, 400);
    }
  }, 5000);
});

// ============ AI ASSISTANT ============
(function () {
  const bubble = document.getElementById('ai-toggle');
  const panel = document.getElementById('ai-panel');
  const closeBtn = document.getElementById('ai-close');
  const form = document.getElementById('ai-form');
  const input = document.getElementById('ai-input');
  const messages = document.getElementById('ai-messages');
  if (!bubble || !panel) return;

  bubble.addEventListener('click', () => {
    panel.classList.toggle('d-none');
    if (!panel.classList.contains('d-none')) {
      panel.style.animation = 'popIn .35s cubic-bezier(.34,1.56,.64,1)';
      input.focus();
    }
  });
  closeBtn && closeBtn.addEventListener('click', () => panel.classList.add('d-none'));

  function addMessage(text, who) {
    const div = document.createElement('div');
    div.className = 'mb-2 d-flex ' + (who === 'user' ? 'justify-content-end' : 'justify-content-start');
    div.style.animation = who === 'user'
      ? 'fadeInRight .35s cubic-bezier(.4,0,.2,1) both'
      : 'fadeInLeft .35s cubic-bezier(.4,0,.2,1) both';
    div.innerHTML = `
      <div class="px-3 py-2 rounded-3 ${who === 'user'
        ? 'bg-primary text-white'
        : 'bg-white border'}"
        style="max-width:85%;font-size:.9rem;line-height:1.4;">
        ${text.replace(/</g,'&lt;').replace(/\n/g,'<br>')}
      </div>`;
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
    return div;
  }

  form && form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const q = input.value.trim();
    if (!q) return;
    addMessage(q, 'user');
    input.value = '';
    const loader = addMessage(
      '<span class="spinner-border spinner-border-sm me-2"></span>Thinking...', 'ai');

    try {
      const res = await fetch('/ai/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': (document.querySelector('input[name="csrf_token"]')?.value) || ''
        },
        body: JSON.stringify({ question: q })
      });
      const data = await res.json();
      loader.remove();
      addMessage(data.answer || 'Sorry, I could not answer that.', 'ai');
    } catch (err) {
      loader.remove();
      addMessage('❌ Network error. Please try again.', 'ai');
    }
  });
})();

// ============ SOCKET.IO NOTIFICATIONS ============
if (typeof io !== 'undefined') {
  const socket = io();
  socket.on('notification', (data) => {
    const el = document.createElement('div');
    el.className = 'alert alert-info shadow-sm border-0';
    el.innerHTML = '<i class="bi bi-bell-fill"></i> ' + data.msg;
    const container = document.getElementById('toast-container');
    if (container) {
      container.appendChild(el);
      setTimeout(() => {
        el.style.animation = 'slideOutRight .4s ease forwards';
        setTimeout(() => el.remove(), 400);
      }, 5000);
    }
  });
}

// ============ CONFETTI ============
window.celebrate = function () {
  const colors = ['#2563eb','#7c3aed','#f59e0b','#10b981','#ef4444','#ec4899'];
  for (let i = 0; i < 90; i++) {
    const p = document.createElement('div');
    p.className = 'confetti-piece';
    p.style.left = Math.random() * 100 + 'vw';
    p.style.background = colors[Math.floor(Math.random() * colors.length)];
    p.style.animationDelay = Math.random() * 0.6 + 's';
    p.style.animationDuration = (2.4 + Math.random() * 1.6) + 's';
    document.body.appendChild(p);
    setTimeout(() => p.remove(), 4200);
  }
};

document.addEventListener('DOMContentLoaded', () => {
  if (document.querySelector('.certificate')) {
    setTimeout(() => window.celebrate && window.celebrate(), 400);
  }
});

// ============ BACK TO TOP ============
(function () {
  const btn = document.createElement('button');
  btn.className = 'back-to-top-btn';
  btn.innerHTML = '<i class="bi bi-arrow-up"></i>';
  btn.setAttribute('aria-label', 'Back to top');
  btn.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
  document.body.appendChild(btn);

  window.addEventListener('scroll', () => {
    btn.classList.toggle('show', window.scrollY > 400);
  });
})();

// ============ HERO CURSOR GLOW ============
(function () {
  const hero = document.querySelector('.hero-lms');
  if (!hero) return;
  const glow = document.createElement('div');
  glow.className = 'hero-cursor-glow';
  glow.style.opacity = '0';
  hero.appendChild(glow);

  hero.addEventListener('mousemove', (e) => {
    const r = hero.getBoundingClientRect();
    glow.style.left = (e.clientX - r.left) + 'px';
    glow.style.top = (e.clientY - r.top) + 'px';
    glow.style.opacity = '1';
  });
  hero.addEventListener('mouseleave', () => { glow.style.opacity = '0'; });
})();

// ============ NAV LINK ACTIVE GLOW ============
(function () {
  document.querySelectorAll('.sidebar-link').forEach(link => {
    link.addEventListener('mouseenter', () => {
      link.style.transition = 'all .25s cubic-bezier(.34,1.56,.64,1)';
    });
  });
})();

// ============ SKELETON LOADING (for slow pages) ============
window.showPageSpinner = function () {
  const spinner = document.createElement('div');
  spinner.className = 'page-spinner show';
  spinner.innerHTML = '<div class="spinner-ring"></div>';
  document.body.appendChild(spinner);
};

// ============ INTERCEPT INTERNAL NAV FOR PAGE FADE ============
document.addEventListener('click', (e) => {
  const link = e.target.closest('a[href]');
  if (!link) return;
  const href = link.getAttribute('href');
  if (!href) return;
  if (href.startsWith('#') || href.startsWith('mailto:') || href.startsWith('tel:')) return;
  if (link.target === '_blank') return;
  if (link.hasAttribute('data-no-transition')) return;
  if (href.startsWith('http') && !href.startsWith(location.origin)) return;

  e.preventDefault();
  document.body.style.transition = 'opacity .25s ease';
  document.body.style.opacity = '0';
  setTimeout(() => { window.location.href = href; }, 200);
});

/* ==========================================================
   PREMIUM ANIMATION PACK
   ========================================================== */

// ============ 1. SCROLL PROGRESS BAR ============
(function () {
  const bar = document.createElement('div');
  bar.className = 'scroll-progress';
  document.body.appendChild(bar);

  window.addEventListener('scroll', () => {
    const scrollTop = window.scrollY;
    const docHeight = document.documentElement.scrollHeight - window.innerHeight;
    const pct = docHeight > 0 ? (scrollTop / docHeight) * 100 : 0;
    bar.style.width = pct + '%';
  }, { passive: true });
})();

// ============ 2. PAGE SLIDE TRANSITIONS ============
(function () {
  // Wrap content for entry animation
  document.addEventListener('DOMContentLoaded', () => {
    const content = document.querySelector('.page-content, main');
    if (content && !content.classList.contains('page-transition-wrap')) {
      content.classList.add('page-transition-wrap');
    }
  });

  // Intercept link clicks for exit animation
  document.addEventListener('click', (e) => {
    const link = e.target.closest('a[href]');
    if (!link) return;
    const href = link.getAttribute('href');
    if (!href || href.startsWith('#') || href.startsWith('mailto:') || href.startsWith('tel:')) return;
    if (link.target === '_blank' || link.hasAttribute('data-no-transition')) return;
    if (href.startsWith('http') && !href.startsWith(location.origin)) return;

    e.preventDefault();
    const content = document.querySelector('.page-content, main');
    if (content) content.classList.add('page-exit');
    setTimeout(() => { window.location.href = href; }, 280);
  });
})();

// ============ 3. MORPHING CARDS ============
(function () {
  document.addEventListener('DOMContentLoaded', () => {
    // Auto-attach to course cards with data-morph attribute
    document.querySelectorAll('[data-morph]').forEach(card => {
      card.addEventListener('click', (e) => {
        if (e.target.closest('a, button')) return;
        const template = card.dataset.morph;
        if (!template) return;
        openMorphModal(card.innerHTML, card.dataset.morphTitle || '');
      });
    });
  });

  function openMorphModal(html, title) {
    let overlay = document.querySelector('.morph-overlay');
    let modal = document.querySelector('.morph-modal');

    if (!overlay) {
      overlay = document.createElement('div');
      overlay.className = 'morph-overlay';
      document.body.appendChild(overlay);

      modal = document.createElement('div');
      modal.className = 'morph-modal';
      modal.innerHTML = `
        <button class="morph-close" aria-label="Close">&times;</button>
        <div class="morph-body"></div>
      `;
      document.body.appendChild(modal);
    }

    modal.querySelector('.morph-body').innerHTML = html;

    overlay.classList.add('active');
    setTimeout(() => modal.classList.add('active'), 20);

    const close = () => {
      modal.classList.remove('active');
      overlay.classList.remove('active');
    };

    overlay.onclick = close;
    modal.querySelector('.morph-close').onclick = close;
    document.addEventListener('keydown', function esc(e) {
      if (e.key === 'Escape') { close(); document.removeEventListener('keydown', esc); }
    });
  }

  window.openMorphModal = openMorphModal;
})();

// ============ 4. CUSTOM CURSOR ============
(function () {
  if (window.matchMedia('(hover: none)').matches) return;
  if (window.matchMedia('(max-width: 991px)').matches) return;

  const dot = document.createElement('div');
  dot.className = 'custom-cursor';
  const ring = document.createElement('div');
  ring.className = 'custom-cursor-ring';
  document.body.appendChild(dot);
  document.body.appendChild(ring);

  let mx = 0, my = 0;
  let rx = 0, ry = 0;

  document.addEventListener('mousemove', (e) => {
    mx = e.clientX;
    my = e.clientY;
    dot.style.left = mx + 'px';
    dot.style.top = my + 'px';
  });

  function animateRing() {
    rx += (mx - rx) * 0.15;
    ry += (my - ry) * 0.15;
    ring.style.left = rx + 'px';
    ring.style.top = ry + 'px';
    requestAnimationFrame(animateRing);
  }
  animateRing();

  // Hover state
  const hoverTargets = 'a, button, .btn, .course-card, .stat-tile, .qa-card, input, textarea, select, [role="button"]';
  document.addEventListener('mouseover', (e) => {
    if (e.target.closest(hoverTargets)) {
      dot.classList.add('hovering');
      ring.classList.add('hovering');
    }
  });
  document.addEventListener('mouseout', (e) => {
    if (e.target.closest(hoverTargets)) {
      dot.classList.remove('hovering');
      ring.classList.remove('hovering');
    }
  });
})();

// ============ 5. PARALLAX SCROLLING ============
(function () {
  const slowEls = document.querySelectorAll('.parallax-slow');
  const fastEls = document.querySelectorAll('.parallax-fast');
  if (!slowEls.length && !fastEls.length) return;

  window.addEventListener('scroll', () => {
    const y = window.scrollY;
    slowEls.forEach(el => el.style.transform = `translateY(${y * 0.15}px)`);
    fastEls.forEach(el => el.style.transform = `translateY(${y * 0.35}px)`);
  }, { passive: true });
})();

// ============ 6. NUMBER ODOMETER ============
window.animateOdometer = function (el, target, suffix) {
  suffix = suffix || '';
  const digits = String(target).split('');
  el.innerHTML = '';
  el.classList.add('odometer');

  digits.forEach((d, i) => {
    const digitWrap = document.createElement('div');
    digitWrap.className = 'digit';
    const stack = document.createElement('div');
    stack.className = 'digit-stack';
    for (let n = 0; n <= 9; n++) {
      const span = document.createElement('span');
      span.textContent = n;
      span.style.height = '1em';
      span.style.lineHeight = '1';
      stack.appendChild(span);
    }
    digitWrap.appendChild(stack);
    el.appendChild(digitWrap);

    // Animate to correct digit
    const finalDigit = parseInt(d);
    setTimeout(() => {
      digitWrap.style.transform = `translateY(-${finalDigit * 100}%)`;
    }, 100 + i * 120);
  });

  if (suffix) {
    const s = document.createElement('span');
    s.textContent = suffix;
    s.style.marginLeft = '2px';
    el.appendChild(s);
  }
};

// Apply to any .odometer[data-target]
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.odometer[data-target]').forEach(el => {
    window.animateOdometer(el, parseInt(el.dataset.target), el.dataset.suffix || '');
  });
});

// ============ 7. MAGNETIC BUTTONS ============
(function () {
  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.btn-primary, .btn-warning, .magnetic').forEach(btn => {
      btn.classList.add('magnetic');
      btn.addEventListener('mousemove', (e) => {
        const r = btn.getBoundingClientRect();
        const x = e.clientX - r.left - r.width / 2;
        const y = e.clientY - r.top - r.height / 2;
        btn.style.transform = `translate(${x * 0.25}px, ${y * 0.25}px)`;
      });
      btn.addEventListener('mouseleave', () => {
        btn.style.transform = '';
      });
    });
  });
})();

// ============ 8. SMOOTH SCROLL WITH EASING ============
(function () {
  document.addEventListener('click', (e) => {
    const link = e.target.closest('a[href^="#"]');
    if (!link) return;
    const target = document.querySelector(link.getAttribute('href'));
    if (!target) return;
    e.preventDefault();
    const offset = 90;
    const top = target.getBoundingClientRect().top + window.scrollY - offset;
    window.scrollTo({ top, behavior: 'smooth' });
  });
})();

// ============ 9. SPLIT TEXT REVEAL ============
window.splitReveal = function (selector) {
  document.querySelectorAll(selector).forEach((el, idx) => {
    const text = el.textContent;
    el.textContent = '';
    [...text].forEach((char, i) => {
      const span = document.createElement('span');
      span.className = 'split-char';
      span.textContent = char === ' ' ? '\u00A0' : char;
      span.style.animationDelay = `${idx * 0.05 + i * 0.03}s`;
      el.appendChild(span);
    });
  });
};

// Auto-apply to hero h1
document.addEventListener('DOMContentLoaded', () => {
  const heroH1 = document.querySelector('.hero-lms h1');
  if (heroH1 && !heroH1.dataset.splitDone) {
    window.splitReveal('.hero-lms h1');
    heroH1.dataset.splitDone = 'true';
  }
});

// ============ 10. LIQUID BLOB BACKGROUND ============
(function () {
  document.addEventListener('DOMContentLoaded', () => {
    if (document.querySelector('.liquid-bg')) return;
    const bg = document.createElement('div');
    bg.className = 'liquid-bg';
    bg.innerHTML = `
      <div class="blob blob-1"></div>
      <div class="blob blob-2"></div>
      <div class="blob blob-3"></div>
    `;
    document.body.appendChild(bg);
  });
})();

// ============ 11. TEXT SCRAMBLE ON HOVER ============
window.scrambleText = function (el, finalText, duration) {
  duration = duration || 800;
  const chars = '!<>-_\\/[]{}—=+*^?#________';
  const start = performance.now();
  const originalText = finalText;

  function update(now) {
    const t = Math.min((now - start) / duration, 1);
    const revealedLength = Math.floor(t * originalText.length);
    let out = '';
    for (let i = 0; i < originalText.length; i++) {
      if (i < revealedLength) out += originalText[i];
      else if (originalText[i] === ' ') out += ' ';
      else out += chars[Math.floor(Math.random() * chars.length)];
    }
    el.textContent = out;
    if (t < 1) requestAnimationFrame(update);
    else el.textContent = originalText;
  }
  requestAnimationFrame(update);
};

// ============ 12. PROGRESS RING HELPER ============
window.setProgressRing = function (el, percent) {
  const ring = el.querySelector('.ring-fill');
  const text = el.querySelector('.ring-text');
  if (!ring) return;
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - percent / 100);
  ring.style.strokeDasharray = `${circumference} ${circumference}`;
  ring.style.strokeDashoffset = circumference;
  setTimeout(() => { ring.style.strokeDashoffset = offset; }, 100);

  if (text) {
    let n = 0;
    const target = percent;
    const step = () => {
      n += Math.max(1, Math.floor(target / 30));
      if (n >= target) { text.textContent = target + '%'; return; }
      text.textContent = n + '%';
      requestAnimationFrame(step);
    };
    step();
  }
};