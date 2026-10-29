document.addEventListener('DOMContentLoaded', function () {
    function syncDragState() {
        const placement = {};
        document.querySelectorAll('.dm-slot').forEach(function (slot) {
            const index = slot.getAttribute('data-index');
            const word = slot.getAttribute('data-word');
            if (index !== null && word) {
                placement[index] = word;
            }
        });
        if (window.dash_clientside) {
            window.dash_clientside.set_props('dm-drag-state', { data: placement });
        }
    }

    function markWordUsed(word) {
        document.querySelectorAll('.dm-word').forEach(function (item) {
            if (item.getAttribute('data-word') === word) {
                item.style.opacity = '0.45';
                item.style.cursor = 'default';
                item.setAttribute('aria-disabled', 'true');
                item.draggable = false;
            }
        });
    }

    document.addEventListener('dragstart', function (event) {
        const wordNode = event.target.closest('.dm-word');
        if (!wordNode) {
            return;
        }
        const word = wordNode.getAttribute('data-word');
        if (!word) {
            return;
        }
        event.dataTransfer.setData('text/plain', word);
        event.dataTransfer.effectAllowed = 'move';
        window.__dm_dragged_word = word;
    });

    document.addEventListener('dragover', function (event) {
        const slot = event.target.closest('.dm-slot');
        if (!slot) {
            return;
        }
        event.preventDefault();
        slot.style.backgroundColor = '#E2E8F0';
        slot.style.borderColor = '#2563EB';
    });

    document.addEventListener('dragleave', function (event) {
        const slot = event.target.closest('.dm-slot');
        if (!slot) {
            return;
        }
        slot.style.backgroundColor = '#FFFFFF';
        slot.style.borderColor = '#0F172A';
    });

    document.addEventListener('drop', function (event) {
        const slot = event.target.closest('.dm-slot');
        if (!slot) {
            return;
        }
        event.preventDefault();
        const word = event.dataTransfer.getData('text/plain') || window.__dm_dragged_word;
        const slotIndex = slot.getAttribute('data-index');
        if (!word || slotIndex === null) {
            return;
        }
        slot.setAttribute('data-word', word);
        slot.textContent = word;
        slot.style.backgroundColor = '#DCFCE7';
        slot.style.borderColor = '#16A34A';
        markWordUsed(word);
        syncDragState();
    });

    document.querySelectorAll('.dm-slot').forEach(function (slot) {
        if (!slot.getAttribute('data-index')) {
            slot.setAttribute('data-index', '0');
        }
        slot.setAttribute('data-word', slot.textContent.trim() === '_____' ? '' : slot.textContent.trim());
    });

    document.querySelectorAll('.dm-word').forEach(function (item) {
        item.setAttribute('data-word', item.textContent.trim());
    });
});
