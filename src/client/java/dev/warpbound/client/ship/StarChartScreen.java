package dev.warpbound.client.ship;

import dev.warpbound.network.NavJumpPayload;
import dev.warpbound.network.StarChartPayload;
import net.fabricmc.fabric.api.client.networking.v1.ClientPlayNetworking;
import net.minecraft.ChatFormatting;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.components.Tooltip;
import net.minecraft.client.gui.screens.Screen;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.util.Mth;

import java.util.ArrayList;
import java.util.List;

/**
 * Карта Империума (табло на стене мостика). Миры канона — только подписи с описанием;
 * нажать можно только на миры корабля (пункты назначения с местом на карте), кроме того, где корабль сейчас.
 */
public class StarChartScreen extends Screen {
    private static final int TEX_W = 1400, TEX_H = 800;
    private static final int INK = 0xFF3C2418, INK_LIGHT = 0xFFE6DCC8, GOLD = 0xFFE8C060, RED = 0xFFB01818, DIM = 0xFF9A8E78;

    /** Миры канона: ключ перевода и место на карте — совпадают с tools/textures/gen_star_map.py. */
    private record World(String key, float x, float y, boolean dark) {
    }

    private static final World[] WORLDS = {
            new World("terra", 0.340f, 0.470f, false), new World("mars", 0.356f, 0.497f, false),
            new World("necromunda", 0.392f, 0.438f, false), new World("cadia", 0.282f, 0.205f, false),
            new World("fenris", 0.168f, 0.272f, false), new World("vigilus", 0.405f, 0.172f, true),
            new World("armageddon", 0.470f, 0.222f, true), new World("prospero", 0.120f, 0.470f, false),
            new World("catachan", 0.300f, 0.780f, false), new World("macragge", 0.800f, 0.700f, false),
            new World("baal", 0.880f, 0.550f, false), new World("nocturne", 0.660f, 0.840f, false),
    };

    /** Надписи областей: ключ, место, цвет. */
    private record Label(String key, float x, float y, int color) {
    }

    private static final Label[] LABELS = {
            new Label("obscurus", 0.03f, 0.19f, INK), new Label("pacificus", 0.05f, 0.40f, INK),
            new Label("solar", 0.30f, 0.60f, INK), new Label("tempestus", 0.14f, 0.86f, INK),
            new Label("ultima", 0.66f, 0.47f, INK), new Label("nihilus", 0.66f, 0.13f, INK_LIGHT),
            new Label("rift", 0.74f, 0.29f, 0xFFF0D0C0), new Label("eye", 0.24f, 0.03f, RED),
    };

    private final StarChartPayload data;
    private int mx, my, mw, mh;
    private final List<Button> markers = new ArrayList<>();
    private World hovered;

    public StarChartScreen(StarChartPayload data) {
        super(Component.translatable("chart.warpbound.title"));
        this.data = data;
    }

    @Override
    protected void init() {
        mw = Math.min(width - 24, 600);
        mh = mw * TEX_H / TEX_W;
        if (mh > height - 60) {
            mh = height - 60;
            mw = mh * TEX_W / TEX_H;
        }
        mx = (width - mw) / 2;
        my = (height - mh) / 2 + 6;
        markers.clear();
        for (int i = 0; i < data.ids().size(); i++) {
            String id = data.ids().get(i);
            boolean here = id.equals(data.current());
            boolean available = data.available().get(i);
            int px = mx + Math.round(data.xs().get(i) * mw), py = my + Math.round(data.ys().get(i) * mh);
            Component name = Component.translatable(data.names().get(i));
            Button b = new Marker(px - 6, py - 6, name, here, id.equals(data.destination()), btn -> {
                ClientPlayNetworking.send(new NavJumpPayload(id));
                onClose();
            });
            MutableComponent tip = name.copy().withStyle(ChatFormatting.GOLD, ChatFormatting.BOLD).append("\n")
                    .append(Component.translatable("chart.warpbound.dest." + id.substring(id.indexOf(':') + 1) + ".desc")
                            .withStyle(ChatFormatting.GRAY)).append("\n");
            if (here) tip.append(Component.translatable("chart.warpbound.here").withStyle(ChatFormatting.AQUA));
            else if (!available) tip.append(Component.translatable("chart.warpbound.unavailable").withStyle(ChatFormatting.DARK_RED));
            else if (!data.canJump()) tip.append(Component.translatable("chart.warpbound.need_orbit").withStyle(ChatFormatting.DARK_GRAY));
            else tip.append(Component.translatable("chart.warpbound.click").withStyle(ChatFormatting.GREEN));
            b.setTooltip(Tooltip.create(tip));
            b.active = !here && data.canJump();
            markers.add(b);
            addRenderableWidget(b);
        }
    }

    @Override
    public void renderBackground(GuiGraphics g, int mouseX, int mouseY, float partialTick) {
        super.renderBackground(g, mouseX, mouseY, partialTick);
        g.drawCenteredString(font, title.copy().withStyle(ChatFormatting.BOLD), width / 2, my - 14, GOLD);
        g.blit(StarChartRenderer.MAP, mx, my, mw, mh, 0, 0, TEX_W, TEX_H, TEX_W, TEX_H);
        float scale = Mth.clamp(mw / 600f, 0.55f, 1f);
        for (Label l : LABELS) {
            text(g, Component.translatable("chart.warpbound.region." + l.key()).withStyle(ChatFormatting.BOLD),
                    mx + l.x() * mw, my + l.y() * mh, l.color(), scale * 0.85f, false);
        }
        hovered = null;
        for (World w : WORLDS) {
            float px = mx + w.x() * mw, py = my + w.y() * mh;
            text(g, Component.translatable("chart.warpbound.world." + w.key()), px + 5, py - 3, w.dark() ? INK_LIGHT : INK, scale * 0.7f, false);
            if (Math.abs(mouseX - px) < 5 && Math.abs(mouseY - py) < 5) hovered = w;
        }
        // легенда и подсказка под картой
        int ly = my + mh + 4;
        Component legend = Component.translatable("chart.warpbound.legend").withStyle(ChatFormatting.ITALIC);
        float ls = Math.min(1f, mw / (float) font.width(legend));
        text(g, legend, mx + (mw - font.width(legend) * ls) / 2f, ly, DIM, ls, false);
    }

    @Override
    public void render(GuiGraphics g, int mouseX, int mouseY, float partialTick) {
        super.render(g, mouseX, mouseY, partialTick);
        if (hovered != null) {
            g.renderComponentTooltip(font, List.of(
                    Component.translatable("chart.warpbound.world." + hovered.key()).withStyle(ChatFormatting.GOLD),
                    Component.translatable("chart.warpbound.world." + hovered.key() + ".desc").withStyle(ChatFormatting.GRAY),
                    Component.translatable("chart.warpbound.canon").withStyle(ChatFormatting.DARK_GRAY)), mouseX, mouseY);
        }
    }

    private void text(GuiGraphics g, Component c, float x, float y, int color, float scale, boolean shadow) {
        g.pose().pushPose();
        g.pose().translate(x, y, 0);
        g.pose().scale(scale, scale, 1);
        g.drawString(font, c, 0, 0, color, shadow);
        g.pose().popPose();
    }

    @Override
    public boolean isPauseScreen() {
        return false;
    }

    /** Мир корабля на карте: пульсирующий знак и подпись. Кнопка — чтобы работали клавиатура и автотест. */
    private class Marker extends Button {
        private final boolean here, target;

        Marker(int x, int y, Component name, boolean here, boolean target, OnPress onPress) {
            super(x, y, 12, 12, name, onPress, DEFAULT_NARRATION);
            this.here = here;
            this.target = target;
        }

        @Override
        protected void renderWidget(GuiGraphics g, int mouseX, int mouseY, float partialTick) {
            int cx = getX() + 6, cy = getY() + 6;
            float t = (System.currentTimeMillis() % 1600) / 1600f;
            int pulse = 3 + Math.round(4 * t);
            int ring = here ? 0x8040E0FF : 0x80FF4020;
            int a = (int) (200 * (1 - t)) << 24;
            g.fill(cx - pulse, cy - pulse, cx + pulse + 1, cy + pulse + 1, (ring & 0xFFFFFF) | a);
            g.fill(cx - 4, cy - 4, cx + 5, cy + 5, 0xFF2A1408);
            g.fill(cx - 3, cy - 3, cx + 4, cy + 4, here ? 0xFF40E0FF : isHovered() ? 0xFFFFE070 : GOLD);
            g.fill(cx - 1, cy - 1, cx + 2, cy + 2, here ? 0xFF0A3040 : 0xFFB01818);
            Component label = here ? getMessage().copy().append(Component.translatable("chart.warpbound.here_short"))
                    : target ? getMessage().copy().append(" ✦") : getMessage();
            // справа от середины карты подпись уходит влево, чтобы не вылезать за рамку
            Component bold = label.copy().withStyle(ChatFormatting.BOLD);
            int tx = cx > mx + mw / 2 ? cx - 8 - font.width(bold) : cx + 8;
            g.drawString(font, bold, tx, cy - 4, here ? 0xFF70F0FF : GOLD, true);
        }
    }
}
