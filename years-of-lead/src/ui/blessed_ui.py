import sys
from blessed import Terminal
from src.game.core import GameState, Phase

term = Terminal()

# Helper for progress bars
def bar(value, max_value, width=10, char_full='█', char_empty='░'):
    filled = int((value / max_value) * width)
    return char_full * filled + char_empty * (width - filled)

class BlessedUI:
    def __init__(self, game_state: GameState):
        self.game_state = game_state
        self.running = True
        self.selected_menu = 0
        self.menu_options = [
            ('A', 'Activism'), ('P', 'Planning'), ('M', 'Move Agent'), ('I', 'Info/Status'),
            ('F', 'Propaganda'), ('E', 'Equip Cell'), ('T', 'Task Menu'), ('S', 'Save Game'),
            ('G', 'Gather Info'), ('D', 'Daily Tasks'), ('R', 'Reports'), ('Q', 'Quit'),
            ('W', 'Wait a day'), ('X', 'Special Ops'), ('H', 'Help/Manual'), ('ESC', 'Cancel')
        ]
        self.agent_keys = list(self.game_state.agents.keys())
        self.location_keys = list(self.game_state.locations.keys())
        self.selected_agent_idx = 0
        self.selected_location_idx = 0
        self.event_log_offset = 0

    def draw(self):
        print(term.home + term.clear)
        self.draw_status_bar()
        self.draw_cell_panel()
        self.draw_location_panel()
        self.draw_mission_panel()
        self.draw_event_log()
        self.draw_command_menu()

    def draw_status_bar(self):
        gs = self.game_state
        phase = gs.current_phase.value.title()
        day = gs.turn_number
        # Use first location as district for now
        district = next(iter(gs.locations.values())).name if gs.locations else 'Unknown'
        # Use first faction as money for now
        money = next(iter(gs.factions.values())).resources.get('money', 0) if gs.factions else 0
        print(term.move_yx(0, 0) + term.bold_white_on_blue(
            f' {district}     Day: {day}     Phase: {phase}     Money: ${money} '.center(term.width, '═')
        ))

    def draw_cell_panel(self):
        gs = self.game_state
        y = 2
        print(term.move_yx(y, 0) + term.bold('╔════════ ACTIVE CELL: Forward House ════════╗'))
        y += 1
        print(term.move_yx(y, 0) + 'NAME         SKILL  LOC         STATUS   TASK')
        # Only show selected agent
        if self.agent_keys:
            idx = self.selected_agent_idx % len(self.agent_keys)
            agent = gs.agents[self.agent_keys[idx]]
            loc = gs.locations[agent.location_id].name[:10] if agent.location_id in gs.locations else agent.location_id
            task = agent.task_queue[0].task_type.value if agent.task_queue else '[None]'
            highlight = term.reverse if idx == self.selected_agent_idx else (lambda x: x)
            print(term.move_yx(y+1, 0) + highlight(f'{agent.name[:12]:12} {agent.skill_level:2}/10  {loc:10} {agent.status:8} {task:12}'))
        print(term.move_yx(y+3, 0) + '╚' + '═'*40 + '╝')

    def draw_location_panel(self):
        gs = self.game_state
        y = 2
        x = 45
        if not self.location_keys:
            return
        idx = self.selected_location_idx % len(self.location_keys)
        loc = gs.locations[self.location_keys[idx]]
        highlight = term.reverse if idx == self.selected_location_idx else (lambda x: x)
        print(term.move_yx(y, x) + highlight(term.bold(f'╔══ LOCATION: {loc.name} [{loc.id.upper()}] ══╗')))
        y += 1
        print(term.move_yx(y, x) + f'Security: {bar(loc.security_level, 10)} ({loc.security_level}/10)')
        y += 1
        print(term.move_yx(y, x) + f'Unrest:   {bar(loc.unrest_level, 10)} ({loc.unrest_level}/10)')
        y += 1
        print(term.move_yx(y, x) + f'Control:  [NEUTRAL]')
        y += 1
        print(term.move_yx(y, x) + f'Presence: Police••• Students•••• Workers•')
        y += 1
        print(term.move_yx(y, x) + '╚' + '═'*32 + '╝')

    def draw_mission_panel(self):
        y = 10
        print(term.move_yx(y, 0) + term.bold('╔════ CURRENT MISSION: Infiltrate Government Office ════╗'))
        y += 1
        print(term.move_yx(y, 0) + 'Risk Level: [███░░] (3/5)  |  Progress: [██░░░░░░░░] (2/10)')
        y += 1
        print(term.move_yx(y, 0) + 'Objectives:')
        y += 1
        print(term.move_yx(y, 0) + '[✓] Scout Location')
        y += 1
        print(term.move_yx(y, 0) + '[✓] Make Contact with Insider')
        y += 1
        print(term.move_yx(y, 0) + '[ ] Obtain Security Credentials')
        y += 1
        print(term.move_yx(y, 0) + '[ ] Access Restricted Area')
        y += 1
        print(term.move_yx(y, 0) + '╚' + '═'*60 + '╝')

    def draw_event_log(self):
        gs = self.game_state
        y = 18
        log = gs.narrative_log
        log_len = len(log)
        visible = 5
        offset = min(self.event_log_offset, max(0, log_len - visible))
        print(term.move_yx(y, 0) + term.bold('╔════════════════════ RECENT EVENTS ═══════════════════╗'))
        for i in range(visible):
            idx = log_len - visible + i - offset
            if 0 <= idx < log_len:
                entry = log[idx]
                print(term.move_yx(y+1+i, 0) + f' > {entry[:60]}')
            else:
                print(term.move_yx(y+1+i, 0) + ' ')
        print(term.move_yx(y+6, 0) + '╚' + '═'*54 + '╝')

    def draw_command_menu(self):
        menu_str = '  '.join([f'[{k}]{v}' for k, v in self.menu_options])
        print(term.move_yx(term.height-2, 0) + term.reverse(menu_str[:term.width]))

    def run(self):
        with term.fullscreen(), term.cbreak(), term.hidden_cursor():
            self.draw()
            while self.running:
                key = term.inkey(timeout=1)
                if key:
                    if key.lower() == 'q':
                        self.running = False
                    elif key.name == 'KEY_UP':
                        self.selected_agent_idx = (self.selected_agent_idx - 1) % max(1, len(self.agent_keys))
                    elif key.name == 'KEY_DOWN':
                        self.selected_agent_idx = (self.selected_agent_idx + 1) % max(1, len(self.agent_keys))
                    elif key.name == 'KEY_LEFT':
                        self.selected_location_idx = (self.selected_location_idx - 1) % max(1, len(self.location_keys))
                    elif key.name == 'KEY_RIGHT':
                        self.selected_location_idx = (self.selected_location_idx + 1) % max(1, len(self.location_keys))
                    elif key.name == 'KEY_PGUP':
                        self.event_log_offset = min(self.event_log_offset + 1, max(0, len(self.game_state.narrative_log) - 5))
                    elif key.name == 'KEY_PGDOWN':
                        self.event_log_offset = max(self.event_log_offset - 1, 0)
                self.draw()

# For manual testing
if __name__ == '__main__':
    gs = GameState()
    ui = BlessedUI(gs)
    ui.run() 