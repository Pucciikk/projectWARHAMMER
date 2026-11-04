package dev.warpbound.client.entity;

import com.mojang.blaze3d.systems.RenderSystem;
import dev.warpbound.Warpbound;
import dev.warpbound.entity.dreadnought.concept.DreadConceptEntity;
import net.fabricmc.fabric.api.client.rendering.v1.HudRenderCallback;
import net.minecraft.client.Minecraft;
import net.minecraft.client.gui.Font;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.item.ItemStack;

/**
 * Интерфейс пилота. От первого лица: изнутри саркофага видна только смотровая щель, по бокам приборы (болты слева, прометий справа), снизу броня.
 * Со стороны: те же показатели небольшой панелью. Доли экрана совпадают с tools/textures/gen_dread_hud.py.
 */
public final class DreadCockpitHud {
    private static final ResourceLocation COCKPIT = Warpbound.id("textures/gui/dread_cockpit.png");
    private static final float[] LEFT = {0.015f, 0.31f, 0.135f, 0.69f}, RIGHT = {0.865f, 0.31f, 0.985f, 0.69f}, BOTTOM = {0.36f, 0.75f, 0.64f, 0.87f};
    private static final int AMBER = 0xFFE8A83A, AMBER_D = 0xFF5A3F14, RED = 0xFFE8452E, GREEN = 0xFF6FD06A, DIM = 0xFF8A7A58;

    private DreadCockpitHud() {
    }

    public static void register() {
        HudRenderCallback.EVENT.register((g, tick) -> {
            Minecraft mc = Minecraft.getInstance();
            if (mc.player == null || !(mc.player.getVehicle() instanceof DreadConceptEntity dread)) return;
            if (mc.options.getCameraType().isFirstPerson()) cockpit(g, mc, dread);
            else outside(g, mc, dread);
        });
    }

    private static void cockpit(GuiGraphics g, Minecraft mc, DreadConceptEntity d) {
        int w = g.guiWidth(), h = g.guiHeight();
        RenderSystem.enableBlend();
        g.blit(COCKPIT, 0, 0, w, h, 0f, 0f, 1920, 1080, 1920, 1080);
        RenderSystem.disableBlend();
        Font font = mc.font;
        // прицел в щели: на топливе горит, без него погас
        int cx = w / 2, cy = h / 2, c = d.fuel() > 0 ? 0xE0E8A83A : 0x60E8A83A;
        g.fill(cx - 9, cy, cx - 3, cy + 1, c);
        g.fill(cx + 4, cy, cx + 10, cy + 1, c);
        g.fill(cx, cy - 8, cx + 1, cy - 3, c);
        g.fill(cx, cy + 4, cx + 1, cy + 9, c);
        g.fill(cx, cy, cx + 1, cy + 1, c);
        // ---- болты слева
        int x0 = (int) (LEFT[0] * w), y0 = (int) (LEFT[1] * h), x1 = (int) (LEFT[2] * w), y1 = (int) (LEFT[3] * h);
        int mid = (x0 + x1) / 2;
        title(g, font, Component.translatable("hud.warpbound.dread.ammo"), mid, y0 + 4);
        icon(g, item("bolt_magazine"), mid, y0 + 16);
        int ammo = d.ammo();
        String count = String.valueOf(ammo);
        g.drawString(font, count, mid - font.width(count) / 2, y0 + 38, ammo == 0 ? blink(mc, RED) : ammo < 30 ? RED : AMBER, false);
        vertical(g, x0 + 6, y0 + 50, x1 - 6, y1 - 6, ammo / (float) DreadConceptEntity.MAX_AMMO, ammo < 30 ? RED : AMBER);
        // ---- прометий справа
        x0 = (int) (RIGHT[0] * w);
        y0 = (int) (RIGHT[1] * h);
        x1 = (int) (RIGHT[2] * w);
        y1 = (int) (RIGHT[3] * h);
        mid = (x0 + x1) / 2;
        title(g, font, Component.translatable("hud.warpbound.dread.fuel"), mid, y0 + 4);
        icon(g, item("promethium_canister"), mid, y0 + 16);
        float fuel = d.fuel() / (float) DreadConceptEntity.MAX_FUEL;
        String percent = Math.round(fuel * 100) + "%";
        g.drawString(font, percent, mid - font.width(percent) / 2, y0 + 38, fuel < 0.15f ? blink(mc, RED) : GREEN, false);
        vertical(g, x0 + 6, y0 + 50, x1 - 6, y1 - 6, fuel, fuel < 0.15f ? RED : GREEN);
        // ---- броня снизу
        x0 = (int) (BOTTOM[0] * w);
        y0 = (int) (BOTTOM[1] * h);
        x1 = (int) (BOTTOM[2] * w);
        y1 = (int) (BOTTOM[3] * h);
        float armor = d.getHealth() / d.getMaxHealth();
        title(g, font, Component.translatable("hud.warpbound.dread.armor"), (x0 + x1) / 2, y0 + 3);
        horizontal(g, x0 + 8, y0 + 14, x1 - 8, y1 - 5, armor, armor < 0.3f ? RED : AMBER);
        // ---- предупреждения в щели
        if (d.fuel() <= 0) center(g, font, Component.translatable("hud.warpbound.dread.no_fuel"), cy + 18, blink(mc, RED));
        else if (ammo == 0) center(g, font, Component.translatable("hud.warpbound.dread.no_ammo"), cy + 18, blink(mc, RED));
        // попадание по машине: кабина вспыхивает красным
        if (d.hurtTime > 0) g.fill(0, 0, w, h, (d.hurtTime * 7) << 24 | 0x901008);
    }

    /** Вид со стороны: щели нет, только небольшая панель. */
    private static void outside(GuiGraphics g, Minecraft mc, DreadConceptEntity d) {
        Font font = mc.font;
        int x = 8, y = g.guiHeight() - 46;
        g.fill(x - 3, y - 3, x + 98, y + 36, 0xB0101012);
        g.drawString(font, Component.translatable("hud.warpbound.dread.ammo").getString() + ": " + d.ammo(), x, y, d.ammo() == 0 ? RED : AMBER, false);
        g.drawString(font, Component.translatable("hud.warpbound.dread.fuel").getString() + ": " + Math.round(100f * d.fuel() / DreadConceptEntity.MAX_FUEL) + "%", x, y + 11, d.fuel() == 0 ? RED : GREEN, false);
        g.drawString(font, Component.translatable("hud.warpbound.dread.armor").getString() + ": " + Math.round(100f * d.getHealth() / d.getMaxHealth()) + "%", x, y + 22, AMBER, false);
    }

    private static ItemStack item(String id) {
        ResourceLocation key = Warpbound.id(id);
        return BuiltInRegistries.ITEM.containsKey(key) ? new ItemStack(BuiltInRegistries.ITEM.get(key)) : ItemStack.EMPTY;
    }

    private static void icon(GuiGraphics g, ItemStack stack, int mid, int y) {
        if (!stack.isEmpty()) g.renderItem(stack, mid - 8, y);
    }

    private static void title(GuiGraphics g, Font font, Component text, int mid, int y) {
        g.drawString(font, text, mid - font.width(text) / 2, y, DIM, false);
    }

    private static void center(GuiGraphics g, Font font, Component text, int y, int color) {
        g.drawString(font, text, g.guiWidth() / 2 - font.width(text) / 2, y, color, false);
    }

    private static int blink(Minecraft mc, int color) {
        return (mc.player.tickCount / 8) % 2 == 0 ? color : AMBER_D;
    }

    /** Столбик снизу вверх, поделён на деления. */
    private static void vertical(GuiGraphics g, int x0, int y0, int x1, int y1, float k, int color) {
        if (y1 <= y0) return;
        g.fill(x0, y0, x1, y1, 0xFF14120E);
        int fill = Math.round((y1 - y0 - 2) * Math.max(0, Math.min(1, k)));
        g.fill(x0 + 1, y1 - 1 - fill, x1 - 1, y1 - 1, color);
        for (int yy = y1 - 5; yy > y0; yy -= 4) g.fill(x0, yy, x1, yy + 1, 0xFF14120E);
    }

    private static void horizontal(GuiGraphics g, int x0, int y0, int x1, int y1, float k, int color) {
        if (y1 <= y0) return;
        g.fill(x0, y0, x1, y1, 0xFF14120E);
        g.fill(x0 + 1, y0 + 1, x0 + 1 + Math.round((x1 - x0 - 2) * Math.max(0, Math.min(1, k))), y1 - 1, color);
        for (int xx = x0 + 6; xx < x1; xx += 6) g.fill(xx, y0, xx + 1, y1, 0xFF14120E);
    }
}
