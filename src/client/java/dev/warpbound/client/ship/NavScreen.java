package dev.warpbound.client.ship;

import dev.warpbound.network.NavJumpPayload;
import dev.warpbound.network.NavStatePayload;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.minecraft.ChatFormatting;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;

/** Навигационный стол: список известных миров, кнопка «Проложить курс» у каждого, кроме текущего. */
public class NavScreen extends Screen {
    private static final int W = 240, ROW = 24;
    private static final int BG = 0xE00C140F, FRAME = 0xFFB08A3C, TEXT = 0xFFE8D9B0, GLOW = 0xFF7CFF9A;

    private final NavStatePayload state;

    public NavScreen(NavStatePayload state) {
        super(Component.translatable("nav.warpbound.title"));
        this.state = state;
    }

    private int height() {
        return 44 + state.ids().size() * ROW;
    }

    @Override
    protected void init() {
        int x = (width - W) / 2, y = (height - height()) / 2;
        for (int i = 0; i < state.ids().size(); i++) {
            String id = state.ids().get(i);
            boolean here = id.equals(state.current());
            Button b = Button.builder(Component.translatable(here ? "nav.warpbound.here" : "nav.warpbound.jump"), btn -> {
                ClientPlayNetworking.send(new NavJumpPayload(id));
                onClose();
            }).bounds(x + W - 96, y + 32 + i * ROW, 84, 20).build();
            b.active = !here;
            addRenderableWidget(b);
        }
    }

    @Override
    public void render(GuiGraphics g, int mouseX, int mouseY, float partialTick) {
        super.render(g, mouseX, mouseY, partialTick);
        int x = (width - W) / 2, y = (height - height()) / 2;
        g.fill(x, y, x + W, y + height(), BG);
        g.renderOutline(x, y, W, height(), FRAME);
        g.drawString(font, title.copy().withStyle(ChatFormatting.BOLD), x + 12, y + 10, TEXT, false);
        for (int i = 0; i < state.ids().size(); i++) {
            boolean here = state.ids().get(i).equals(state.current());
            g.drawString(font, Component.literal(here ? "◉ " : "○ ").append(Component.translatable(state.names().get(i))),
                    x + 12, y + 38 + i * ROW, here ? GLOW : TEXT, false);
        }
    }

    @Override
    public boolean isPauseScreen() {
        return false;
    }
}
