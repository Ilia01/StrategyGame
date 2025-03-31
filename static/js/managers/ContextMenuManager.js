export class ContextMenuManager {
    constructor(game, entityManager) {
        this.game = game;
        this.entityManager = entityManager;
        this.contextMenu = null;
        this.contextMenuTarget = null;
    }

    showContextMenu(event) {
        this.hideContextMenu();

        const target = event.target.closest('.map-cell, .entity');
        if (!target) {
            console.log('No valid target found for context menu');
            return;
        }

        this.contextMenu = document.createElement('div');
        this.contextMenu.className = 'context-menu';
        this.contextMenuTarget = target;

        const rect = target.getBoundingClientRect();
        const x = event.clientX;
        const y = event.clientY;

        this.contextMenu.style.left = `${x}px`;
        this.contextMenu.style.top = `${y}px`;

        const menuItems = this.getContextMenuItems(target);
        if (menuItems) {
            const tempContainer = document.createElement('div');
            tempContainer.innerHTML = menuItems;
            while (tempContainer.firstChild) {
                this.contextMenu.appendChild(tempContainer.firstChild);
            }
        }

        document.body.appendChild(this.contextMenu);
        this.adjustContextMenuPosition();
        this.bindMenuItemEvents();
    }

    hideContextMenu() {
        if (this.contextMenu) {
            this.contextMenu.remove();
            this.contextMenu = null;
            this.contextMenuTarget = null;
        }
    }

    adjustContextMenuPosition() {
        if (!this.contextMenu) return;

        const rect = this.contextMenu.getBoundingClientRect();
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;

        if (rect.right > viewportWidth) {
            this.contextMenu.style.left = `${viewportWidth - rect.width}px`;
        }

        if (rect.bottom > viewportHeight) {
            this.contextMenu.style.top = `${viewportHeight - rect.height}px`;
        }
    }

    bindMenuItemEvents() {
        const menuItemElements = this.contextMenu.querySelectorAll('.context-menu-item');
        menuItemElements.forEach(item => {
            item.addEventListener('click', (e) => {
                e.stopPropagation();
                const action = item.dataset.action;
                this.handleContextMenuAction(action);
            });
        });
    }

    getContextMenuItems(target) {
        const isCurrentPlayer = this.game.state.isCurrentPlayer(this.game.state.currentPlayer);
        const items = [];

        if (target.classList.contains('entity')) {
            items.push(...this.getEntityMenuItems(target, isCurrentPlayer));
        } else if (target.classList.contains('map-cell')) {
            items.push(...this.getMapCellMenuItems(target, isCurrentPlayer));
        }

        return items.join('');
    }

    getEntityMenuItems(target, isCurrentPlayer) {
        const entityType = target.classList.contains('unit') ? 'unit' : 'building';
        const entityId = target.dataset[`${entityType}Id`];
        const entity = entityType === 'unit'
            ? this.game.state.getUnit(entityId)
            : this.game.state.getBuilding(entityId);

        if (!entity) return [];

        const isOwnedByPlayer = entity.player_id === this.game.state.currentPlayer;
        const items = [];

        if (entityType === 'unit') {
            if (isOwnedByPlayer) {
                items.push(`
                    <div class="context-menu-item" data-action="move">
                        <i class="fas fa-walking"></i>Move
                    </div>
                    <div class="context-menu-item" data-action="attack">
                        <i class="fas fa-crosshairs"></i>Attack
                    </div>
                `);
            } else {
                items.push(`
                    <div class="context-menu-item" data-action="attack">
                        <i class="fas fa-crosshairs"></i>Attack
                    </div>
                `);
            }
        } else if (entityType === 'building' && isOwnedByPlayer) {
            items.push(`
                <div class="context-menu-item" data-action="train">
                    <i class="fas fa-user-plus"></i>Train Unit
                </div>
            `);
        }

        items.push(`
            <div class="context-menu-divider"></div>
            <div class="context-menu-item" data-action="info">
                <i class="fas fa-info-circle"></i>Info
            </div>
        `);

        return items;
    }

    getMapCellMenuItems(target, isCurrentPlayer) {
        const x = parseInt(target.dataset.x);
        const y = parseInt(target.dataset.y);
        const cell = this.game.state.getMapCell(x, y);

        if (isCurrentPlayer && cell && cell.terrain !== 'water' && cell.terrain !== 'mountain') {
            return [`
                <div class="context-menu-item" data-action="build">
                    <i class="fas fa-hammer"></i>Build
                </div>
            `];
        }
        return [];
    }

    handleContextMenuAction(action) {
        if (!this.contextMenuTarget) return;

        const actions = {
            move: () => {
                if (this.contextMenuTarget.classList.contains('unit')) {
                    const x = parseInt(this.contextMenuTarget.dataset.x);
                    const y = parseInt(this.contextMenuTarget.dataset.y);
                    this.entityManager.selectAtPosition(x, y);
                }
            },
            attack: () => {
                if (this.contextMenuTarget.classList.contains('unit')) {
                    const x = parseInt(this.contextMenuTarget.dataset.x);
                    const y = parseInt(this.contextMenuTarget.dataset.y);
                    this.entityManager.selectAtPosition(x, y);
                }
            },
            build: () => {
                if (this.contextMenuTarget.classList.contains('map-cell')) {
                    const x = parseInt(this.contextMenuTarget.dataset.x);
                    const y = parseInt(this.contextMenuTarget.dataset.y);
                    this.game.uiManager.showBuildingModal(x, y);
                }
            },
            train: () => {
                if (this.contextMenuTarget.classList.contains('building')) {
                    this.game.uiManager.showTrainingModal();
                }
            },
            info: () => {
                const x = parseInt(this.contextMenuTarget.dataset.x);
                const y = parseInt(this.contextMenuTarget.dataset.y);
                this.entityManager.selectAtPosition(x, y);
            }
        };

        if (actions[action]) {
            actions[action]();
        }

        this.hideContextMenu();
    }
} 