(function () {
  'use strict';

  var D = window.REPORT_DATA;
  if (!D) { return; }

  var $ = function (sel) { return document.querySelector(sel); };
  var el = function (tag, cls, html) {
    var n = document.createElement(tag);
    if (cls) { n.className = cls; }
    if (html != null) { n.innerHTML = html; }
    return n;
  };
  var esc = function (s) {
    return String(s).replace(/[&<>"]/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
    });
  };

  /* ---------- Icons ---------- */
  var ICONS = {
    target: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.4" fill="currentColor" stroke="none"/>',
    package: '<path d="M12 3l8 4.5v9L12 21l-8-4.5v-9L12 3z"/><path d="M4 7.5l8 4.5 8-4.5M12 12v9"/>',
    heart: '<path d="M12 20s-7-4.4-7-9.4A4.1 4.1 0 0 1 12 8a4.1 4.1 0 0 1 7 2.6c0 5-7 9.4-7 9.4z"/>',
    rocket: '<path d="M5 15l-2 5 5-2"/><path d="M9 19s-2-1-3-4c2-3 5-7 9-9 3-1.5 6-1 6-1s.5 3-1 6c-2 4-6 7-9 9c-3 1-4-1-4-1z"/><circle cx="14.5" cy="9.5" r="1.5"/>',
    zap: '<path d="M13 2L4 14h6l-1 8 9-12h-6l1-8z"/>',
    shield: '<path d="M12 3l8 3v6c0 5-3.5 8.2-8 9-4.5-.8-8-4-8-9V6l8-3z"/><path d="M9 12l2 2 4-4"/>',
    palette: '<path d="M12 21a9 9 0 1 1 9-9c0 2.5-2 3.5-3.8 3.5H15a2 2 0 0 0-1.4 3.4A1.9 1.9 0 0 1 12 21z"/><circle cx="8" cy="10" r="1.1" fill="currentColor" stroke="none"/><circle cx="12" cy="7.5" r="1.1" fill="currentColor" stroke="none"/><circle cx="16" cy="9.5" r="1.1" fill="currentColor" stroke="none"/>',
    layers: '<path d="M12 3l9 5-9 5-9-5 9-5z"/><path d="M3 13l9 5 9-5"/>',
    link: '<path d="M10 13a5 5 0 0 0 7 0l2-2a5 5 0 0 0-7-7l-1 1"/><path d="M14 11a5 5 0 0 0-7 0l-2 2a5 5 0 0 0 7 7l1-1"/>'
  };

  /* ---------- 动态文案（避免写死数字，同步后自动跟随数据） ---------- */
  (function () {
    var get = function (label) {
      for (var i = 0; i < D.overview.length; i++) {
        if (D.overview[i].label === label) { return D.overview[i]; }
      }
      return null;
    };
    var n = D.projects.length;
    var lines = D.techStack.reduce(function (a, b) { return a + b.lines; }, 0);
    var online = D.projects.filter(function (p) { return !!p.online; }).length;
    var days = get('使用天数');
    var projSub = $('#projectsSub');
    if (projSub) { projSub.textContent = n + ' 个完整交付的项目，以及它们各自的体量'; }
    var tlSub = $('#timelineSub');
    if (tlSub) {
      tlSub.textContent = '从首次启动到现在，' + D.timeline.length + ' 个关键节点';
    }
    var lead = $('#heroSubLead');
    if (lead) {
      var txt = (days ? days.value + ' 天、' : '') + n + ' 个完整项目、' +
        lines.toLocaleString() + ' 行代码';
      if (online > 0) { txt += '，其中 ' + online + ' 个已上线'; }
      txt += '。';
      lead.textContent = txt;
    }
  })();

  /* ---------- Hero meta ---------- */
  (function () {
    var box = $('#heroMeta');
    if (!box) { return; }
    [
      ['账号', D.meta.owner],
      ['统计区间', D.meta.period],
      ['生成日期', D.meta.generatedAt],
      ['项目', D.projects.length + ' 个'],
      ['代码', D.techStack.reduce(function (a, b) { return a + b.lines; }, 0).toLocaleString() + ' 行']
    ].forEach(function (p) {
      box.appendChild(el('span', 'hero-chip', esc(p[0]) + ' <b>' + esc(p[1]) + '</b>'));
    });
  })();

  /* ---------- Stats ---------- */
  (function () {
    var box = $('#stats');
    if (!box) { return; }
    D.overview.forEach(function (s) {
      var card = el('div', 'stat reveal');
      card.innerHTML =
        '<div class="stat-value" data-to="' + s.value + '">0<span class="unit">' + esc(s.unit) + '</span></div>' +
        '<div class="stat-label">' + esc(s.label) + '</div>' +
        '<div class="stat-desc">' + esc(s.desc) + '</div>';
      box.appendChild(card);
    });
  })();

  /* ---------- Timeline ---------- */
  (function () {
    var box = $('#timelineList');
    if (!box) { return; }
    D.timeline.forEach(function (t, i) {
      var li = el('li', 'tl-item reveal');
      if (i === D.timeline.length - 1) { li.setAttribute('data-last', '1'); }
      li.innerHTML =
        '<span class="tl-dot"></span>' +
        '<div class="tl-head"><span class="tl-date">' + esc(t.date) + '</span>' +
        '<span class="tl-tag">' + esc(t.tag) + '</span></div>' +
        '<h3 class="tl-title">' + esc(t.title) + '</h3>' +
        '<p class="tl-desc">' + esc(t.desc) + '</p>';
      box.appendChild(li);
    });
  })();

  /* ---------- Projects ---------- */
  (function () {
    var box = $('#projectList');
    if (!box) { return; }
    D.projects.forEach(function (p) {
      // 只有标注 lines 的计入行数；标注 size 的（PPT、图片等二进制产物）不计
      var totalLines = p.files.reduce(function (a, f) { return a + (f.size ? 0 : (f.lines || 0)); }, 0);
      var card = el('article', 'project reveal');
      card.setAttribute('data-color', p.color);

      var html = '';
      html += '<div class="project-top">';
      html += '  <div class="pj-row">';
      html += '    <div><h3 class="pj-name">' + esc(p.name) + '</h3><div class="pj-sub">' + esc(p.subtitle) + '</div></div>';
      html += '    <div class="pj-status">' + esc(p.status) + '</div>';
      html += '  </div>';
      html += '  <div class="pj-meta">';
      html += '    <span><i></i>' + esc(p.time) + '</span>';
      html += '    <span><i></i>耗时 ' + esc(p.duration) + '</span>';
      html += '    <span><i></i>' + (totalLines > 0
        ? '共 ' + totalLines.toLocaleString() + ' 行'
        : '纯视觉产物') + '</span>';
      html += '    <span><i></i>' + p.files.length + ' 个文件</span>';
      html += '  </div>';
      html += '  <p class="pj-summary">' + esc(p.summary) + '</p>';
      html += '  <div class="pj-tags">' + p.stack.map(function (s) { return '<span class="tag">' + esc(s) + '</span>'; }).join('') + '</div>';
      if (p.online) {
        html += '  <a class="pj-online" href="' + esc(p.online) + '" target="_blank" rel="noopener">' +
          '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' + ICONS.link + '</svg>' +
          '线上地址 <b>' + esc(p.online) + '</b></a>';
      }
      html += '</div>';

      html += '<div class="project-body">';
      html += '  <div>';
      html += '    <div class="pj-block-title">核心实现</div>';
      html += '    <ul class="pj-list">' + p.highlights.map(function (h) { return '<li>' + esc(h) + '</li>'; }).join('') + '</ul>';
      if (p.contentScale) {
        html += '    <div class="pj-block-title" style="margin-top:26px">内容体量</div>';
        html += '    <div class="scale">' + p.contentScale.map(function (c) {
          return '<div class="scale-item"><b>' + c.value + '</b><span>' + esc(c.label) + '</span></div>';
        }).join('') + '</div>';
      }
      html += '  </div>';
      html += '  <div>';
      html += '    <div class="pj-block-title">文件清单</div>';
      html += '    <div class="file-list">' + p.files.map(function (f) {
        return '<div class="file-row"><div><div class="fname">' + esc(f.name) + '</div>' +
          '<div class="fdesc">' + esc(f.desc) + '</div></div>' +
          '<div class="flines">' + (f.size
            ? esc(f.size)
            : (f.lines || 0).toLocaleString() + ' 行') + '</div></div>';
      }).join('') + '</div>';
      html += '  </div>';
      html += '</div>';

      card.innerHTML = html;
      box.appendChild(card);
    });
  })();

  /* ---------- Donut ---------- */
  (function () {
    var svg = $('#donut');
    var legend = $('#donutLegend');
    if (!svg) { return; }
    var R = 15.9155, C = 100;
    var offset = 25; // start at 12 o'clock
    var total = D.techStack.reduce(function (a, b) { return a + b.lines; }, 0);

    D.techStack.forEach(function (t, i) {
      var seg = el('circle', '');
      seg.setAttribute('cx', '21');
      seg.setAttribute('cy', '21');
      seg.setAttribute('r', String(R));
      seg.setAttribute('stroke', t.color);
      seg.setAttribute('stroke-dasharray', '0 ' + C);
      seg.setAttribute('stroke-dashoffset', String(offset));
      seg.dataset.len = String(t.share);
      seg.style.transition = 'stroke-dasharray 1.1s cubic-bezier(.22,1,.36,1) ' + (i * 0.09 + 0.1) + 's';
      svg.appendChild(seg);
      offset -= t.share;
      if (offset < 0) { offset += C; }
    });

    var tf = $('#donutTotal');
    if (tf) { tf.textContent = total.toLocaleString(); }

    if (legend) {
      D.techStack.forEach(function (t) {
        var row = el('div', 'lg-row');
        row.innerHTML =
          '<span class="lg-swatch" style="background:' + t.color + '"></span>' +
          '<span class="lg-name">' + esc(t.name) + '</span>' +
          '<span class="lg-pct">' + t.share.toFixed(1) + '%</span>' +
          '<span class="lg-note">' + esc(t.note) + '</span>';
        legend.appendChild(row);
      });
    }

    window.__drawStack = function () {
      Array.prototype.forEach.call(svg.querySelectorAll('circle'), function (c) {
        var v = parseFloat(c.dataset.len || '0');
        c.setAttribute('stroke-dasharray', v + ' ' + (C - v));
      });
      Array.prototype.forEach.call(document.querySelectorAll('.bar-fill'), function (b) {
        b.style.width = b.dataset.w + '%';
      });
    };
  })();

  /* ---------- Bars ---------- */
  (function () {
    var box = $('#bars');
    if (!box) { return; }
    D.techStack.forEach(function (t) {
      var b = el('div', 'bar');
      b.innerHTML =
        '<div class="bar-head"><span class="bar-name">' + esc(t.name) +
        ' <span style="color:var(--muted);font-weight:400;font-size:12.5px">· ' + esc(t.note) + '</span></span>' +
        '<span class="bar-val">' + t.lines.toLocaleString() + ' 行 · ' + t.share.toFixed(1) + '%</span></div>' +
        '<div class="bar-track"><div class="bar-fill" data-w="' + t.share + '" style="background:linear-gradient(90deg,' +
        t.color + ',' + t.color + 'bb)"></div></div>';
      box.appendChild(b);
    });
  })();

  /* ---------- Insights ---------- */
  (function () {
    var box = $('#insights');
    if (!box) { return; }
    D.insights.forEach(function (it) {
      var c = el('div', 'insight reveal');
      c.innerHTML =
        '<div class="insight-icon"><svg viewBox="0 0 24 24">' + (ICONS[it.icon] || ICONS.target) + '</svg></div>' +
        '<h3>' + esc(it.title) + '</h3>' +
        '<p>' + esc(it.desc) + '</p>';
      box.appendChild(c);
    });
  })();

  /* ---------- Workspaces ---------- */
  (function () {
    var box = $('#wsRows');
    if (!box) { return; }
    D.workspaces.forEach(function (w) {
      var tr = document.createElement('tr');
      tr.innerHTML =
        '<td><span class="wname">' + esc(w.name) + '</span></td>' +
        '<td><span class="wtime">' + esc(w.created) + '</span></td>' +
        '<td><span class="wstatus" data-tone="' + esc(w.tone) + '">' + esc(w.status) + '</span></td>' +
        '<td><span class="wnote">' + esc(w.note) + '</span></td>';
      box.appendChild(tr);
    });
  })();

  /* ---------- Footer ---------- */
  (function () {
    var f = $('#footerMeta');
    if (f) {
      f.textContent = '账号 ' + D.meta.owner + ' · 统计区间 ' + D.meta.period + ' · 生成于 ' + D.meta.generatedAt;
    }
  })();

  /* ---------- Count-up ---------- */
  function countUp(node) {
    var to = parseFloat(node.dataset.to || '0');
    var unit = node.querySelector('.unit');
    var suffix = unit ? unit.outerHTML : '';
    var start = null, dur = 1100;
    function step(ts) {
      if (!start) { start = ts; }
      var p = Math.min((ts - start) / dur, 1);
      var v = Math.round(to * (1 - Math.pow(1 - p, 3)));
      node.innerHTML = v.toLocaleString() + suffix;
      if (p < 1) { requestAnimationFrame(step); }
    }
    requestAnimationFrame(step);
  }

  /* ---------- Reveal on scroll ---------- */
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var io = null;
  if ('IntersectionObserver' in window) {
    io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) { return; }
        var n = e.target;
        n.classList.add('in');
        var cv = n.classList.contains('stat') ? n.querySelector('.stat-value') : null;
        if (cv && !reduce) { countUp(cv); } else if (cv) { cv.innerHTML = parseFloat(cv.dataset.to).toLocaleString() + (cv.querySelector('.unit') ? cv.querySelector('.unit').outerHTML : ''); }
        io.unobserve(n);
      });
    }, { threshold: 0.15, rootMargin: '0px 0px -40px 0px' });
  }

  Array.prototype.forEach.call(document.querySelectorAll('.reveal'), function (n) {
    if (io) { io.observe(n); } else { n.classList.add('in'); }
  });

  /* ---------- Draw charts when stack section appears ---------- */
  var stack = $('#stack');
  if (stack && 'IntersectionObserver' in window && window.__drawStack) {
    var drawn = false;
    new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting && !drawn) {
          drawn = true;
          setTimeout(window.__drawStack, 120);
        }
      });
    }, { threshold: 0.25 }).observe(stack);
  } else if (window.__drawStack) {
    setTimeout(window.__drawStack, 400);
  }
})();
