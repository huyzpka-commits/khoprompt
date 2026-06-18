(function () {
  'use strict';

  const state = {
    prompts: [],
    filter: 'all',
    query: '',
    sort: 'newest',
    page: 1,
    perPage: 20,
  };

  const elements = {
    grid: document.getElementById('prompt-grid'),
    count: document.getElementById('result-count'),
    empty: document.getElementById('empty-state'),
    search: document.getElementById('search-input'),
    filters: document.getElementById('filters'),
    sort: document.getElementById('sort-select'),
    perPage: document.getElementById('per-page'),
    pagination: document.getElementById('pagination'),
    prevPage: document.getElementById('prev-page'),
    nextPage: document.getElementById('next-page'),
    pageInfo: document.getElementById('page-info'),
    modal: document.getElementById('prompt-modal'),
    modalImg: document.getElementById('modal-img'),
    modalTitle: document.getElementById('modal-title'),
    modalDesc: document.getElementById('modal-desc'),
    modalBadge: document.getElementById('modal-badge'),
    modalTags: document.getElementById('modal-tags'),
    modalDate: document.getElementById('modal-date'),
    modalPrompt: document.getElementById('modal-prompt'),
    copyBtn: document.getElementById('copy-btn'),
    copyFeedback: document.getElementById('copy-feedback'),
    year: document.getElementById('year'),
  };

  const TOOL_LABELS = {
    gemini: 'Gemini',
    chatgpt: 'ChatGPT',
    flux: 'Flux',
    midjourney: 'Midjourney',
    'stable-diffusion': 'Stable Diffusion',
    'nano-banana': 'Nano Banana',
    other: 'Khác',
    unknown: 'Không rõ',
  };

  async function loadPrompts() {
    try {
      const response = await fetch('data/prompts.json');
      if (!response.ok) throw new Error('Failed to load prompts');
      state.prompts = await response.json();
      render();
    } catch (error) {
      console.error('KhoPrompt error:', error);
      elements.grid.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon">⚠️</div>
          <h2>Không thể tải dữ liệu</h2>
          <p>Vui lòng kiểm tra kết nối hoặc file data/prompts.json.</p>
        </div>
      `;
      elements.count.textContent = '0 prompt';
    }
  }

  function normalize(str) {
    return (str || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
  }

  function getFilteredPrompts() {
    const query = normalize(state.query);
    let items = state.prompts.filter((p) => {
      const matchesTool = state.filter === 'all' || p.tool === state.filter;
      const matchesQuery =
        !query ||
        normalize(p.title).includes(query) ||
        normalize(p.desc).includes(query) ||
        normalize(p.prompt).includes(query) ||
        normalize(p.tags.join(' ')).includes(query) ||
        normalize(TOOL_LABELS[p.tool]).includes(query);
      return matchesTool && matchesQuery;
    });

    switch (state.sort) {
      case 'popular':
        items.sort((a, b) => b.popular - a.popular);
        break;
      case 'name':
        items.sort((a, b) => normalize(a.title).localeCompare(normalize(b.title)));
        break;
      case 'newest':
      default:
        items.sort((a, b) => new Date(b.date) - new Date(a.date));
        break;
    }

    return items;
  }

  function render() {
    const items = getFilteredPrompts();
    const total = items.length;
    elements.count.textContent = `${total} prompt`;

    if (total === 0) {
      elements.grid.innerHTML = '';
      elements.empty.classList.remove('hidden');
      elements.pagination.hidden = true;
      return;
    }

    elements.empty.classList.add('hidden');

    const totalPages = Math.max(1, Math.ceil(total / state.perPage));
    if (state.page > totalPages) {
      state.page = totalPages;
    }

    const start = (state.page - 1) * state.perPage;
    const pageItems = items.slice(start, start + state.perPage);

    elements.grid.innerHTML = pageItems.map((p) => createCardHTML(p)).join('');

    document.querySelectorAll('.prompt-card').forEach((card) => {
      card.addEventListener('click', () => openModal(Number(card.dataset.id)));
    });

    document.querySelectorAll('.card-image img').forEach((img) => {
      img.addEventListener('error', () => {
        img.src = 'data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 400 300%22%3E%3Crect width=%22400%22 height=%22300%22 fill=%22%232b3647%22/%3E%3Ctext x=%22200%22 y=%22150%22 font-family=%22sans-serif%22 font-size=%2216%22 fill=%22%23ffffff%22 text-anchor=%22middle%22 opacity=%220.6%22%3E%E1%BA%A2nh%20kh%C3%B4ng%20t%E1%BB%93n%20t%E1%BA%A1i%3C/text%3E%3C/svg%3E';
      });
    });

    renderPagination(totalPages, total);
  }

  function renderPagination(totalPages, total) {
    if (totalPages <= 1) {
      elements.pagination.hidden = true;
      return;
    }
    elements.pagination.hidden = false;
    elements.prevPage.disabled = state.page <= 1;
    elements.nextPage.disabled = state.page >= totalPages;
    elements.pageInfo.textContent = `Trang ${state.page} / ${totalPages} (${total} mục)`;
  }

  function goToPage(page) {
    state.page = Math.max(1, page);
    render();
    elements.grid.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function createCardHTML(p) {
    const label = TOOL_LABELS[p.tool] || p.tool;
    return `
      <article class="prompt-card" data-id="${p.id}" tabindex="0" role="button" aria-label="Xem prompt: ${p.title}">
        <div class="card-image">
          <img src="${p.image}" alt="Demo ${p.title}" loading="lazy">
          <span class="tool-badge ${p.tool}">${label}</span>
          <div class="card-overlay">
            <span>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <rect width="14" height="14" x="8" y="8" rx="2" ry="2"></rect>
                <path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"></path>
              </svg>
              Sao chép prompt
            </span>
          </div>
        </div>
        <div class="card-body">
          <h3 class="card-title">${p.title}</h3>
          <p class="card-desc">${p.desc}</p>
          <div class="card-meta">
            <div class="card-tags">
              ${p.tags.slice(0, 3).map((tag) => `<span class="card-tag">#${tag}</span>`).join('')}
            </div>
            <time datetime="${p.date}">${formatDate(p.date)}</time>
          </div>
        </div>
      </article>
    `;
  }

  function formatDate(dateString) {
    const d = new Date(dateString);
    return d.toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit', year: 'numeric' });
  }

  function openModal(id) {
    const p = state.prompts.find((item) => item.id === id);
    if (!p) return;

    elements.modalImg.src = p.image;
    elements.modalImg.alt = `Demo ${p.title}`;
    elements.modalTitle.textContent = p.title;
    elements.modalDesc.textContent = p.desc;
    elements.modalBadge.textContent = TOOL_LABELS[p.tool] || p.tool;
    elements.modalBadge.className = `tool-badge ${p.tool}`;
    elements.modalTags.innerHTML = p.tags.map((tag) => `<span>#${tag}</span>`).join('');
    elements.modalDate.textContent = formatDate(p.date);
    elements.modalPrompt.value = p.prompt;
    elements.copyFeedback.textContent = '';

    elements.modal.hidden = false;
    document.body.style.overflow = 'hidden';
    elements.copyBtn.focus();
  }

  function closeModal() {
    elements.modal.hidden = true;
    document.body.style.overflow = '';
  }

  async function copyPrompt() {
    const text = elements.modalPrompt.value;
    try {
      await navigator.clipboard.writeText(text);
      elements.copyFeedback.textContent = 'Đã sao chép!';
    } catch (err) {
      elements.modalPrompt.select();
      document.execCommand('copy');
      elements.copyFeedback.textContent = 'Đã sao chép!';
    }
    setTimeout(() => {
      elements.copyFeedback.textContent = '';
    }, 2000);
  }

  function initEvents() {
    elements.search.addEventListener('input', (e) => {
      state.query = e.target.value.trim();
      state.page = 1;
      render();
    });

    elements.filters.addEventListener('click', (e) => {
      if (!e.target.classList.contains('filter-btn')) return;
      elements.filters.querySelectorAll('.filter-btn').forEach((btn) => btn.classList.remove('active'));
      e.target.classList.add('active');
      state.filter = e.target.dataset.filter;
      state.page = 1;
      render();
    });

    elements.sort.addEventListener('change', (e) => {
      state.sort = e.target.value;
      state.page = 1;
      render();
    });

    elements.perPage.addEventListener('change', (e) => {
      state.perPage = Math.max(1, parseInt(e.target.value, 10) || 20);
      state.page = 1;
      render();
    });

    elements.prevPage.addEventListener('click', () => goToPage(state.page - 1));
    elements.nextPage.addEventListener('click', () => goToPage(state.page + 1));

    elements.modal.addEventListener('click', (e) => {
      if (e.target.hasAttribute('data-close-modal')) {
        closeModal();
      }
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && !elements.modal.hidden) {
        closeModal();
      }
    });

    elements.copyBtn.addEventListener('click', copyPrompt);

    elements.year.textContent = new Date().getFullYear();
  }

  function init() {
    initEvents();
    loadPrompts();
  }

  init();
})();
