package dev.warpbound.client.shipyard;

import dev.warpbound.network.ShipyardActionPayload;
import dev.warpbound.network.ShipyardStatePayload;
import dev.warpbound.shipyard.ShipClass;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.minecraft.ChatFormatting;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.ItemStack;

/**
 * Экран верфи: схема этапов корабля, поставки текущего этапа, кнопки «Сдать», «Начать этап», «Старт».
 * Пока идёт работа, экран сам раз в секунду просит у сервера свежее состояние.
 */
public class ShipyardScreen extends Screen {
    private static final int W = 300, H = 210;
    private static final int BG = 0xE0141210, FRAME = 0xFFB08A3C, TEXT = 0xFFE8D9B0, DIM = 0xFF8A7A5A, OK = 0xFF7CFF9A;

    private ShipyardStatePayload state;
    private Button deposit, start, launch;
    private int refreshTicks;

    public ShipyardScreen(ShipyardStatePayload state) {
        super(Component.translatable("shipyard.warpbound.title"));
        this.state = state;
    }

    /** Новое состояние от сервера: обновить открытый экран или открыть новый. */
    public static void receive(ShipyardStatePayload payload) {
        Minecraft mc = Minecraft.getInstance();
        if (mc.screen instanceof ShipyardScreen screen && screen.state.pos().equals(payload.pos())) {
            screen.state = payload;
            screen.updateButtons();
        } else {
            mc.setScreen(new ShipyardScreen(payload));
        }
    }

    @Override
    protected void init() {
        int x = (width - W) / 2, y = (height - H) / 2;
        int by = y + H - 28;
        deposit = addRenderableWidget(Button.builder(Component.translatable("shipyard.warpbound.deposit"),
                b -> send(ShipyardActionPayload.DEPOSIT)).bounds(x + 12, by, 88, 20).build());
        start = addRenderableWidget(Button.builder(Component.translatable("shipyard.warpbound.start_stage"),
                b -> send(ShipyardActionPayload.START_STAGE)).bounds(x + 106, by, 88, 20).build());
        launch = addRenderableWidget(Button.builder(Component.translatable("shipyard.warpbound.launch"),
                b -> send(ShipyardActionPayload.LAUNCH)).bounds(x + 200, by, 88, 20).build());
        updateButtons();
    }

    private void send(int action) {
        ClientPlayNetworking.send(new ShipyardActionPayload(state.pos(), action));
    }

    private boolean allStagesDone() {
        return state.stage() >= state.stages().size();
    }

    private boolean requirementsMet() {
        for (int i = 0; i < state.counts().size(); i++) {
            if (deposited(i) < state.counts().get(i)) return false;
        }
        return true;
    }

    private int deposited(int i) {
        return i < state.deposited().size() ? state.deposited().get(i) : 0;
    }

    private void updateButtons() {
        if (deposit == null) return;
        boolean building = state.buildLeft() > 0;
        deposit.active = !allStagesDone() && !building && !requirementsMet();
        start.active = !allStagesDone() && !building && requirementsMet();
        launch.active = allStagesDone() && !state.launching();
    }

    @Override
    public void tick() {
        if ((state.buildLeft() > 0 || state.launching()) && ++refreshTicks >= 20) {
            refreshTicks = 0;
            send(ShipyardActionPayload.REFRESH);
        }
    }

    @Override
    public void render(GuiGraphics g, int mouseX, int mouseY, float partialTick) {
        super.render(g, mouseX, mouseY, partialTick);
        int x = (width - W) / 2, y = (height - H) / 2;
        g.fill(x, y, x + W, y + H, BG);
        g.renderOutline(x, y, W, H, FRAME);
        g.drawString(font, title.copy().withStyle(ChatFormatting.BOLD), x + 12, y + 10, TEXT, false);
        g.drawString(font, Component.translatable(state.className()), x + 12, y + 22, DIM, false);

        // Этапы: слева, как схема постройки
        int sy = y + 40;
        for (int i = 0; i < state.stages().size(); i++) {
            boolean done = i < state.stage(), current = i == state.stage();
            String mark = done ? "■ " : current ? "▶ " : "□ ";
            int color = done ? OK : current ? TEXT : DIM;
            g.drawString(font, Component.literal(mark).append(Component.translatable(state.stages().get(i))), x + 12, sy, color, false);
            sy += 12;
        }

        // Поставки текущего этапа: справа
        int rx = x + 150, ry = y + 40;
        if (allStagesDone()) {
            g.drawString(font, Component.translatable(state.launching()
                    ? "shipyard.warpbound.launching" : "shipyard.warpbound.ready"), rx, ry, OK, false);
            return;
        }
        g.drawString(font, Component.translatable("shipyard.warpbound.requirements"), rx, ry, TEXT, false);
        ry += 14;
        for (int i = 0; i < state.items().size(); i++) {
            ItemStack icon = new ItemStack(new ShipClass.Requirement(state.items().get(i), 0).icon());
            g.renderItem(icon, rx, ry - 4);
            int have = deposited(i), need = state.counts().get(i);
            g.drawString(font, have + " / " + need, rx + 20, ry, have >= need ? OK : TEXT, false);
            if (mouseX >= rx && mouseX < rx + 16 && mouseY >= ry - 4 && mouseY < ry + 12) {
                g.renderTooltip(font, icon, mouseX, mouseY);
            }
            ry += 18;
        }

        // Ход работы над этапом
        if (state.buildLeft() > 0 && state.buildTotal() > 0) {
            int barY = y + H - 44, barW = W - 24;
            float done = 1f - state.buildLeft() / (float) state.buildTotal();
            g.fill(x + 12, barY, x + 12 + barW, barY + 6, 0xFF2A241A);
            g.fill(x + 12, barY, x + 12 + (int) (barW * done), barY + 6, FRAME);
            g.drawString(font, Component.translatable("shipyard.warpbound.building", state.buildLeft() / 20),
                    x + 12, barY - 11, TEXT, false);
        }
    }

    @Override
    public boolean isPauseScreen() {
        return false;
    }
}
