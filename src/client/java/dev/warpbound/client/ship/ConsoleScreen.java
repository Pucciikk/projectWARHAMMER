package dev.warpbound.client.ship;

import dev.warpbound.Warpbound;
import dev.warpbound.network.ShipConsoleActionPayload;
import dev.warpbound.network.ShipConsolePayload;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.minecraft.ChatFormatting;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.util.Mth;

/**
 * Командный пульт мостика — экран когитатора: вкладки «Состояние», «Навигация», «Поле Геллера», «Реактор».
 * Пока открыт, раз в секунду просит у сервера свежие данные.
 */
public class ConsoleScreen extends Screen {
    private static final ResourceLocation BG = Warpbound.id("textures/gui/command_console.png");
    private static final int W = 320, H = 208;
    private static final int TEXT = 0xFFE8D9B0, DIM = 0xFF8FA58F, GREEN = 0xFF7CFF9A, AMBER = 0xFFFFB347, RED = 0xFFFF5040,
            BLUE = 0xFF6EC8FF, VIOLET = 0xFFB27CFF, BAR_BG = 0xFF0E1A10, FRAME = 0xFF4A6A4A;
    private static final String[] STATES = {"orbit", "entering", "transit", "exiting"};
    private static final String[] MODES = {"idle", "normal", "overdrive", "scram"};

    private enum Tab { STATUS, FLIGHT, NAV, GELLER, REACTOR }

    private ShipConsolePayload data;
    private Tab tab = Tab.STATUS;
    private int ticks;

    public ConsoleScreen(ShipConsolePayload data) {
        super(Component.translatable("console.warpbound.title"));
        this.data = data;
    }

    /** Пришли свежие данные: обновить, не закрывая экран. */
    public static void receive(ShipConsolePayload payload) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.screen instanceof ConsoleScreen screen) {
            screen.data = payload;
            screen.rebuildWidgets();
        } else if (payload.open()) {
            mc.setScreen(new ConsoleScreen(payload));
        }
    }

    private int x0() {
        return (width - W) / 2;
    }

    private int y0() {
        return (height - H) / 2;
    }

    private static void send(int action, float value, String target) {
        ClientPlayNetworking.send(new ShipConsoleActionPayload(action, value, target));
    }

    @Override
    protected void init() {
        int x = x0(), y = y0();
        if (data.docked()) {
            // корабль на стапеле: только выход в космос
            Button launch = Button.builder(Component.translatable("console.warpbound.launch"),
                    btn -> send(ShipConsoleActionPayload.LAUNCH, 0, "")).bounds(x + 40, y + 150, W - 80, 22).build();
            launch.active = data.missing().isEmpty() && !data.launching();
            addRenderableWidget(launch);
            return;
        }
        Tab[] tabs = Tab.values();
        for (int i = 0; i < tabs.length; i++) {
            Tab t = tabs[i];
            Button b = Button.builder(Component.translatable("console.warpbound.tab." + t.name().toLowerCase()), btn -> {
                tab = t;
                rebuildWidgets();
            }).bounds(x + 13 + i * 59, y + 13, 58, 17).build();
            b.active = tab != t;
            addRenderableWidget(b);
        }
        switch (tab) {
            case FLIGHT -> initFlight(x, y);
            case NAV -> initNav(x, y);
            case GELLER -> initGeller(x, y);
            case REACTOR -> initReactor(x, y);
            default -> {
            }
        }
    }

    private void initFlight(int x, int y) {
        int[] actions = {ShipConsoleActionPayload.ENGINES, ShipConsoleActionPayload.GELLER, ShipConsoleActionPayload.SHUTTERS};
        String[] keys = {"engines", "geller", "shutters"};
        boolean orbit = data.state() == 0;
        for (int i = 0; i < 3; i++) {
            boolean on = (data.flight() & (1 << i)) != 0;
            int action = actions[i];
            Button b = Button.builder(Component.translatable("console.warpbound.flight." + keys[i] + (on ? ".off" : ".on")),
                    btn -> send(action, 0, "")).bounds(x + W - 130, y + 50 + i * 26, 114, 20).build();
            b.active = orbit || i == 2;
            addRenderableWidget(b);
        }
        Button rift = Button.builder(Component.translatable("console.warpbound.flight.rift").withStyle(ChatFormatting.DARK_RED),
                btn -> send(ShipConsoleActionPayload.OPEN_RIFT, 0, "")).bounds(x + 16, y + 150, W - 32, 22).build();
        rift.active = data.missing().isEmpty();
        addRenderableWidget(rift);
    }

    private void initNav(int x, int y) {
        boolean orbit = data.state() == 0;
        for (int i = 0; i < data.ids().size(); i++) {
            String id = data.ids().get(i);
            boolean here = id.equals(data.location());
            Button b = Button.builder(Component.translatable(here ? "nav.warpbound.here" : "nav.warpbound.jump"),
                    btn -> send(ShipConsoleActionPayload.PLOT_COURSE, 0, id)).bounds(x + W - 112, y + 58 + i * 22, 96, 18).build();
            b.active = orbit && !here;
            addRenderableWidget(b);
        }
    }

    private void initGeller(int x, int y) {
        for (int i = 0; i <= 4; i++) {
            float v = i / 4f;
            Button b = Button.builder(Component.literal(i * 25 + "%"), btn -> send(ShipConsoleActionPayload.GELLER_POWER, v, ""))
                    .bounds(x + 16 + i * 46, y + 128, 44, 18).build();
            b.active = Math.abs(data.gellerPower() - v) > 0.01f;
            addRenderableWidget(b);
        }
        Button boost = Button.builder(Component.translatable("console.warpbound.boost"),
                btn -> send(ShipConsoleActionPayload.FIELD_BOOST, 0, "")).bounds(x + 16, y + 160, 140, 20).build();
        boost.active = data.boostCooldown() == 0 && data.reactorMode() != 3;
        addRenderableWidget(boost);
    }

    private void initReactor(int x, int y) {
        for (int i = 0; i < MODES.length; i++) {
            int mode = i;
            Button b = Button.builder(Component.translatable("console.warpbound.mode." + MODES[i]),
                    btn -> send(ShipConsoleActionPayload.REACTOR_MODE, mode, "")).bounds(x + 16 + i * 72, y + 46, 70, 18).build();
            b.active = data.reactorMode() != i;
            addRenderableWidget(b);
        }
        Button flush = Button.builder(Component.translatable("console.warpbound.flush"),
                btn -> send(ShipConsoleActionPayload.COOLANT_FLUSH, 0, "")).bounds(x + 16, y + 166, 150, 20).build();
        flush.active = data.flushCooldown() == 0;
        addRenderableWidget(flush);
    }

    @Override
    public void tick() {
        if (++ticks % 20 == 0) send(ShipConsoleActionPayload.REFRESH, 0, "");
    }

    @Override
    public void renderBackground(GuiGraphics g, int mouseX, int mouseY, float partialTick) {
        super.renderBackground(g, mouseX, mouseY, partialTick);
        g.blit(BG, x0(), y0(), 0, 0, W, H, W, H);
    }

    @Override
    public void render(GuiGraphics g, int mouseX, int mouseY, float partialTick) {
        super.render(g, mouseX, mouseY, partialTick);
        int x = x0(), y = y0();
        // строка заголовка внизу рамки: имя корабля и экипаж на борту
        String head = "+++ " + data.shipName() + " +++";
        g.drawString(font, Component.literal(head).withStyle(ChatFormatting.BOLD), x + 16, y + H - 9 - 8, AMBER, false);
        g.drawString(font, Component.translatable("console.warpbound.crew", data.crew()), x + W - 90, y + H - 17, DIM, false);
        if (data.docked()) {
            renderDocked(g, x, y);
            return;
        }
        switch (tab) {
            case FLIGHT -> renderFlight(g, x, y);
            case STATUS -> renderStatus(g, x, y);
            case NAV -> renderNav(g, x, y);
            case GELLER -> renderGeller(g, x, y);
            case REACTOR -> renderReactor(g, x, y);
        }
    }

    private void renderStatus(GuiGraphics g, int x, int y) {
        int ty = y + 42;
        g.drawString(font, Component.translatable("console.warpbound.state",
                Component.translatable("console.warpbound.state." + STATES[Mth.clamp(data.state(), 0, 3)])), x + 16, ty, GREEN, false);
        g.drawString(font, Component.translatable("console.warpbound.location", destName(data.location())), x + 16, ty + 12, TEXT, false);
        if (!data.destination().isEmpty()) {
            g.drawString(font, Component.translatable("console.warpbound.course", destName(data.destination())), x + 16, ty + 24, AMBER, false);
            bar(g, x + 170, ty + 24, 130, data.progress(), AMBER);
        }
        int by = ty + 38;
        gauge(g, x + 16, by, "console.warpbound.field", data.field(), BLUE);
        gauge(g, x + 16, by + 18, "console.warpbound.storm", data.storm(), VIOLET);
        gauge(g, x + 16, by + 36, "console.warpbound.power", data.power(), AMBER);
        gauge(g, x + 16, by + 54, "console.warpbound.heat", data.heat(), heatColor(data.heat()));
        gauge(g, x + 16, by + 72, "console.warpbound.radiation", data.radiation(), data.radiation() > 0.05f ? RED : GREEN);
        warnings(g, x + 16, y + H - 32);
    }

    private void renderDocked(GuiGraphics g, int x, int y) {
        g.drawString(font, Component.translatable("console.warpbound.docked").withStyle(ChatFormatting.BOLD), x + 16, y + 16, AMBER, false);
        g.drawString(font, Component.translatable("console.warpbound.docked.stages", data.stage(), data.stages()), x + 16, y + 44, TEXT, false);
        bar(g, x + 16, y + 58, W - 32, data.stages() == 0 ? 0 : data.stage() / (float) data.stages(), GREEN);
        Component hint = data.launching() ? Component.translatable("console.warpbound.docked.launching")
                : data.missing().isEmpty() ? Component.translatable("console.warpbound.docked.ready")
                : Component.translatable(data.missing());
        int c = data.launching() ? BLUE : data.missing().isEmpty() ? GREEN : DIM;
        int ly = y + 80;
        for (var line : font.split(hint, W - 32)) {
            g.drawString(font, line, x + 16, ly, c, false);
            ly += 11;
        }
    }

    private void renderFlight(GuiGraphics g, int x, int y) {
        g.drawString(font, Component.translatable("console.warpbound.flight.title"), x + 16, y + 38, AMBER, false);
        String[] keys = {"engines", "geller", "shutters"};
        for (int i = 0; i < 3; i++) {
            boolean on = (data.flight() & (1 << i)) != 0;
            g.drawString(font, Component.literal(on ? "■ " : "□ ").append(Component.translatable("console.warpbound.flight." + keys[i])),
                    x + 16, y + 56 + i * 26, on ? GREEN : DIM, false);
        }
        boolean course = !data.destination().isEmpty();
        g.drawString(font, Component.literal(course ? "■ " : "□ ").append(course
                        ? Component.translatable("console.warpbound.course", destName(data.destination()))
                        : Component.translatable("flight.warpbound.need.course")),
                x + 16, y + 56 + 3 * 26, course ? GREEN : DIM, false);
        if (!data.missing().isEmpty()) {
            g.drawString(font, Component.translatable(data.missing()), x + 16, y + 176, AMBER, false);
        }
    }

    private void renderNav(GuiGraphics g, int x, int y) {
        g.drawString(font, Component.translatable(data.state() == 0 ? "console.warpbound.nav.pick" : "console.warpbound.nav.in_warp"),
                x + 16, y + 42, data.state() == 0 ? GREEN : VIOLET, false);
        for (int i = 0; i < data.ids().size(); i++) {
            boolean here = data.ids().get(i).equals(data.location());
            boolean target = data.ids().get(i).equals(data.destination());
            g.drawString(font, Component.literal(here ? "◉ " : target ? "➤ " : "○ ").append(Component.translatable(data.names().get(i))),
                    x + 18, y + 63 + i * 22, here ? GREEN : target ? AMBER : TEXT, false);
        }
    }

    private void renderGeller(GuiGraphics g, int x, int y) {
        gauge(g, x + 16, y + 44, "console.warpbound.field", data.field(), BLUE);
        gauge(g, x + 16, y + 64, "console.warpbound.storm", data.storm(), VIOLET);
        float supply = data.gellerPower() * data.power();
        gauge(g, x + 16, y + 84, "console.warpbound.supply", supply, GREEN);
        g.drawString(font, Component.translatable("console.warpbound.allocation", Math.round(data.gellerPower() * 100)),
                x + 16, y + 114, TEXT, false);
        Component cd = data.boostCooldown() > 0
                ? Component.translatable("console.warpbound.cooldown", data.boostCooldown() / 20)
                : Component.translatable("console.warpbound.boost_ready");
        g.drawString(font, cd, x + 164, y + 166, data.boostCooldown() > 0 ? DIM : GREEN, false);
    }

    private void renderReactor(GuiGraphics g, int x, int y) {
        g.drawString(font, Component.translatable("console.warpbound.mode",
                Component.translatable("console.warpbound.mode." + MODES[Mth.clamp(data.reactorMode(), 0, 3)])), x + 16, y + 72, AMBER, false);
        gauge(g, x + 16, y + 86, "console.warpbound.power", data.power(), AMBER);
        gauge(g, x + 16, y + 106, "console.warpbound.heat", data.heat(), heatColor(data.heat()));
        // отметка порога утечки радиации
        int bx = x + 16 + 110, bw = 150;
        int mark = bx + Math.round(bw * 0.7f);
        g.fill(mark, y + 104, mark + 1, y + 117, RED);
        gauge(g, x + 16, y + 126, "console.warpbound.radiation", data.radiation(), data.radiation() > 0.05f ? RED : GREEN);
        Component cd = data.flushCooldown() > 0
                ? Component.translatable("console.warpbound.cooldown", data.flushCooldown() / 20)
                : Component.translatable("console.warpbound.flush_ready");
        g.drawString(font, cd, x + 174, y + 172, data.flushCooldown() > 0 ? DIM : GREEN, false);
        warnings(g, x + 16, y + 148);
    }

    private void warnings(GuiGraphics g, int x, int y) {
        boolean blink = (ticks / 10) % 2 == 0;
        if (data.heat() > 0.92f && blink) {
            g.drawString(font, Component.translatable("console.warpbound.warn.critical").withStyle(ChatFormatting.BOLD), x, y, RED, false);
        } else if (data.radiation() > 0.05f) {
            g.drawString(font, Component.translatable("console.warpbound.warn.radiation"), x, y, AMBER, false);
        } else if (data.field() < 0.3f && blink) {
            g.drawString(font, Component.translatable("console.warpbound.warn.field").withStyle(ChatFormatting.BOLD), x, y, VIOLET, false);
        }
    }

    private Component destName(String id) {
        for (int i = 0; i < data.ids().size(); i++) {
            if (data.ids().get(i).equals(id)) return Component.translatable(data.names().get(i));
        }
        return Component.literal(id);
    }

    private static int heatColor(float heat) {
        return heat > 0.9f ? RED : heat > 0.7f ? AMBER : GREEN;
    }

    private void gauge(GuiGraphics g, int x, int y, String key, float value, int color) {
        g.drawString(font, Component.translatable(key), x, y + 2, TEXT, false);
        bar(g, x + 110, y, 150, value, color);
        g.drawString(font, Math.round(value * 100) + "%", x + 266, y + 2, color, false);
    }

    private static void bar(GuiGraphics g, int x, int y, int w, float value, int color) {
        g.fill(x, y, x + w, y + 11, BAR_BG);
        g.renderOutline(x, y, w, 11, FRAME);
        int fill = Math.round((w - 2) * Mth.clamp(value, 0, 1));
        g.fill(x + 1, y + 1, x + 1 + fill, y + 10, color);
        for (int i = x + 1; i < x + 1 + fill; i += 4) g.fill(i, y + 1, i + 1, y + 10, 0x33000000); // деления
    }

    @Override
    public boolean isPauseScreen() {
        return false;
    }
}
