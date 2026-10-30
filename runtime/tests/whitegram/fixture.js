class Demo extends wg.BasePlugin {
    onLoad() {
        wg.chat.addButton({ id: 'tama_btn', hookName: 'tama_open' });
        wg.settings.registerPage({ id: 'pet', controls: [] });
        wg.on('tama_open', () => wg.ui.actionSheet('Pet', 'Choose', ['Feed', 'Play', 'Sleep'], (index) => {
            if (index === 0) { wg.vibrate(); wg.setStorage('tamagotchi_state', 'fed'); }
        }));
        this.timer = setInterval(() => {}, 1000);
    }
    onUnload() { clearInterval(this.timer); wg.chat.removeView('tama_btn'); }
}
wg.registerPlugin(new Demo());
