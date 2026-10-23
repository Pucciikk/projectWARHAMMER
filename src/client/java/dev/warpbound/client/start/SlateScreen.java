package dev.warpbound.client.start;

import dev.warpbound.Warpbound;
import net.minecraft.ChatFormatting;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.client.resources.sounds.SimpleSoundInstance;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.util.FormattedCharSequence;

import java.util.List;

/** Экран инфопланшета: запись печатается зелёным по экрану, как на старом когитаторе. */
public class SlateScreen extends Screen {
    private static final ResourceLocation TEXTURE = Warpbound.id("textures/gui/slate.png");
    private static final int W = 256, H = 160;
    /** Букв в тик: запись появляется постепенно, клик показывает её сразу. */
    private static final int CHARS_PER_TICK = 3;

    private final String memory;
    private String text;
    private int shown;

    public SlateScreen(String memory) {
        super(Component.translatable("slate.warpbound." + memory + ".title"));
        this.memory = memory;
    }

    @Override
    protected void init() {
        text = Component.translatable("slate.warpbound." + memory + ".text").getString();
        minecraft.getSoundManager().play(SimpleSoundInstance.forUI(SoundEvents.BEACON_ACTIVATE, 2f, 0.3f));
    }

    @Override
    public void tick() {
        if (shown < text.length()) shown = Math.min(text.length(), shown + CHARS_PER_TICK);
    }

    @Override
    public void render(GuiGraphics g, int mouseX, int mouseY, float partialTick) {
        super.render(g, mouseX, mouseY, partialTick);
        int x = (width - W) / 2, y = (height - H) / 2;
        g.blit(TEXTURE, x, y, 0, 0, W, H, W, H);
        g.drawString(font, title.copy().withStyle(ChatFormatting.BOLD), x + 16, y + 18, 0xFF7CFF9A, false);
        int ty = y + 32;
        String visible = text.substring(0, shown) + (shown < text.length() || (System.currentTimeMillis() / 400) % 2 == 0 ? "_" : "");
        for (String paragraph : visible.split("\n")) {
            List<FormattedCharSequence> lines = font.split(Component.literal(paragraph), W - 32);
            for (FormattedCharSequence line : lines) {
                if (ty > y + H - 26) break;
                g.drawString(font, line, x + 16, ty, 0xFF4FD870, false);
                ty += 10;
            }
            ty += 3;
        }
    }

    @Override
    public boolean mouseClicked(double mouseX, double mouseY, int button) {
        if (shown < text.length()) {
            shown = text.length();
            return true;
        }
        onClose();
        return true;
    }

    @Override
    public boolean isPauseScreen() {
        return false;
    }
}
