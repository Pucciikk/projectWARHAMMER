package dev.warpbound.client.industry;

import com.mojang.blaze3d.systems.RenderSystem;
import dev.warpbound.Warpbound;
import dev.warpbound.core.ChainContentList;
import dev.warpbound.industry.ChainMachineBlockEntity;
import dev.warpbound.industry.machine.ChainMachineMenu;
import dev.warpbound.industry.machine.MachineRecipe;
import net.minecraft.ChatFormatting;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.screens.inventory.AbstractContainerScreen;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.material.Fluid;
import net.minecraft.world.level.material.Fluids;
import org.jetbrains.annotations.Nullable;

import java.util.ArrayList;
import java.util.List;

/**
 * Окно машины цепочки в стиле Механикус. Фон и детали — tools/textures/gen_machine_gui.py, координаты деталей заданы там же.
 * Слоты и манометры расставляются по описанию машины; в пустых слотах и баках бледно видно, что нужно по выбранному рецепту.
 */
public class ChainMachineScreen extends AbstractContainerScreen<ChainMachineMenu> {
    private static final ResourceLocation BG = Warpbound.id("textures/gui/machine.png"), PARTS = Warpbound.id("textures/gui/machine_parts.png");
    private static final int BG_W = 232, BG_H = 212, PARTS_SIZE = 256;
    private static final int GAUGE_Y = 26, GAUGE_H = 64, TANK_W = 14, ENERGY_X = 10, IN_TANK_X = 26, TANK_STEP = 16, RIGHT = 222;
    private static final int ARROW_X = 104, ARROW_Y = 51, ARROW_W = 36, ARROW_H = 14;
    private static final int STATUS_X = 24, STATUS_Y = 101, LAMP_X = 13, LAMP_Y = 101;
    private static final int PICK_Y = 98, PREV_X = 174, ICON_X = 188, NEXT_X = 208;
    private static final int TEXT_GREEN = 0xFF66E08A, TEXT_DIM = 0xFF2F8A52, TITLE = 0xFF2A1C08;
    /** Сколько единиц влезает в бак: то же, что MachineTanks.CAPACITY в миллибакетах. */
    private static final int TANK_MB = 16000;

    public ChainMachineScreen(ChainMachineMenu menu, Inventory inventory, Component title) {
        super(menu, inventory, title);
        imageWidth = ChainMachineMenu.WIDTH;
        imageHeight = ChainMachineMenu.HEIGHT;
    }

    private void click(int id) {
        minecraft.gameMode.handleInventoryButtonClick(menu.containerId, id);
    }

    private boolean pickable() {
        return menu.init().recipes().size() > 1;
    }

    private boolean inPrev(double mx, double my) {
        return pickable() && mx >= leftPos + PREV_X && mx < leftPos + PREV_X + 10 && my >= topPos + PICK_Y && my < topPos + PICK_Y + 14;
    }

    private boolean inNext(double mx, double my) {
        return pickable() && mx >= leftPos + NEXT_X && mx < leftPos + NEXT_X + 10 && my >= topPos + PICK_Y && my < topPos + PICK_Y + 14;
    }

    private boolean inIcon(double mx, double my) {
        return mx >= leftPos + ICON_X && mx < leftPos + ICON_X + 16 && my >= topPos + PICK_Y - 1 && my < topPos + PICK_Y + 15;
    }

    @Override
    public boolean mouseClicked(double mx, double my, int button) {
        if (button == 0 && inPrev(mx, my)) {
            click(0);
            return true;
        }
        if (button == 0 && inNext(mx, my)) {
            click(1);
            return true;
        }
        return super.mouseClicked(mx, my, button);
    }

    /** Рецепт, который сейчас показывать: выбранный игроком, иначе идущий, иначе единственный. */
    @Nullable
    private MachineRecipe shownRecipe() {
        List<MachineRecipe> all = menu.init().recipes();
        int selected = menu.value(ChainMachineMenu.D_SELECTED), active = menu.value(ChainMachineMenu.D_ACTIVE);
        if (selected >= 0 && selected < all.size()) return all.get(selected);
        if (active >= 0 && active < all.size()) return all.get(active);
        return all.size() == 1 ? all.get(0) : null;
    }

    private int status() {
        return menu.value(ChainMachineMenu.D_STATUS);
    }

    private float time(float partialTick) {
        return minecraft.level == null ? 0 : minecraft.level.getGameTime() + partialTick;
    }

    private void part(GuiGraphics g, int x, int y, int u, int v, int w, int h) {
        // g.fill и предметы сбрасывают смешивание: без этого блик стекла становится сплошным белым
        RenderSystem.enableBlend();
        g.blit(PARTS, x, y, u, v, w, h, PARTS_SIZE, PARTS_SIZE);
    }

    private int outTankX(int i) {
        return RIGHT - TANK_W - i * TANK_STEP;
    }

    @Override
    protected void renderBg(GuiGraphics g, float partialTick, int mouseX, int mouseY) {
        RenderSystem.enableBlend();
        int x = leftPos, y = topPos;
        g.blit(BG, x, y, 0, 0, BG_W, BG_H, BG_W, BG_H);
        ChainMachineMenu.Init init = menu.init();
        // ---- слоты: выходы в латунной рамке
        for (int i = 0; i < menu.machineSlots(); i++) {
            Slot s = menu.slots.get(i);
            if (i < init.slotsIn()) part(g, x + s.x - 1, y + s.y - 1, 0, 0, 18, 18);
            else part(g, x + s.x - 3, y + s.y - 3, 20, 0, 22, 22);
        }
        // ---- энергия и топливо
        if (init.usesEnergy()) energy(g, x + ENERGY_X, y + GAUGE_Y);
        // ---- баки
        MachineRecipe shown = shownRecipe();
        float t = time(partialTick);
        for (int i = 0; i < init.tanksIn(); i++) {
            Fluid hint = shown != null && i < shown.fluidsIn().size() ? shown.fluidsIn().get(i).fluid() : null;
            tank(g, x + IN_TANK_X + i * TANK_STEP, y + GAUGE_Y, i, hint, t);
        }
        for (int i = 0; i < init.tanksOut(); i++) {
            Fluid hint = shown != null && i < shown.fluidsOut().size() ? shown.fluidsOut().get(i).fluid() : null;
            tank(g, x + outTankX(i), y + GAUGE_Y, ChainMachineBlockEntity.TANKS_IN + i, hint, t);
        }
        // ---- стрелка хода и шестерни
        boolean running = status() == ChainMachineMenu.STATUS_RUNNING;
        int frame = running ? (int) (t / 2) & 7 : 0, frameBack = running ? 7 - ((int) (t / 2) & 7) : 0;
        int row = running ? 124 : 148;
        part(g, x + ARROW_X + 2, y + ARROW_Y - 24, frame * 24, row, 22, 22);
        part(g, x + ARROW_X + 16, y + ARROW_Y - 22, frameBack * 24, row, 22, 22);
        part(g, x + ARROW_X, y + ARROW_Y, 0, 90, ARROW_W, ARROW_H);
        if (init.generator()) {
            part(g, x + ARROW_X + 11, y + ARROW_Y + 18, 108, 90, 14, 14);
            int burn = menu.value(ChainMachineMenu.D_BURN) * 14 / 1000;
            if (running) burn = Math.max(burn, 7);
            if (burn > 0) part(g, x + ARROW_X + 11, y + ARROW_Y + 18 + 14 - burn, 108, 106 + 14 - burn, 14, burn);
        }
        int fill = ARROW_W * Math.min(1000, menu.value(ChainMachineMenu.D_PROGRESS)) / 1000;
        if (fill > 0) part(g, x + ARROW_X, y + ARROW_Y, 0, 106, fill, ARROW_H);
        // ---- лампа: мигает, только когда машина требует внимания
        int status = status();
        int lamp = switch (status) {
            case ChainMachineMenu.STATUS_RUNNING -> 0;
            case ChainMachineMenu.STATUS_IDLE, ChainMachineMenu.STATUS_BUFFER_FULL -> 3;
            case ChainMachineMenu.STATUS_OUTPUT_FULL -> 1;
            default -> ((int) t / 10) % 2 == 0 ? 2 : 3;
        };
        part(g, x + LAMP_X, y + LAMP_Y, 40 + lamp * 9, 90, 8, 8);
        // ---- выбор рецепта
        if (pickable()) {
            part(g, x + PREV_X, y + PICK_Y, 80, inPrev(mouseX, mouseY) ? 106 : 90, 10, 14);
            part(g, x + NEXT_X, y + PICK_Y, 92, inNext(mouseX, mouseY) ? 106 : 90, 10, 14);
            int selected = menu.value(ChainMachineMenu.D_SELECTED);
            if (selected < 0) {
                g.drawCenteredString(font, Component.translatable("gui.warpbound.machine.auto"), x + ICON_X + 8, y + PICK_Y + 3, TEXT_GREEN);
            } else if (shown != null) {
                renderRecipeIcon(g, shown, x + ICON_X, y + PICK_Y - 1);
            }
        }
    }

    private void renderRecipeIcon(GuiGraphics g, MachineRecipe r, int x, int y) {
        if (!r.itemsOut().isEmpty()) {
            g.renderItem(new ItemStack(r.itemsOut().get(0).item()), x, y);
        } else if (!r.fluidsOut().isEmpty()) {
            int c = 0xFF000000 | colour(r.fluidsOut().get(0).fluid());
            g.fill(x + 2, y + 2, x + 14, y + 14, c);
            g.renderOutline(x + 2, y + 2, 12, 12, 0xFF000000);
        }
    }

    private void energy(GuiGraphics g, int x, int y) {
        part(g, x, y, 32, 24, 12, GAUGE_H);
        int h = 60 * Math.min(1000, menu.value(ChainMachineMenu.D_ENERGY)) / 1000;
        if (h > 0) part(g, x + 2, y + 2 + 60 - h, 46, 26 + 60 - h, 8, h);
    }

    private void tank(GuiGraphics g, int x, int y, int index, @Nullable Fluid hint, float time) {
        part(g, x, y, 0, 24, TANK_W, GAUGE_H);
        int amount = menu.value(ChainMachineMenu.D_TANKS + index * 2);
        Fluid fluid = fluid(index);
        if (amount > 0 && fluid != Fluids.EMPTY) {
            int h = Math.max(1, 60 * Math.min(amount, TANK_MB) / TANK_MB);
            int c = colour(fluid);
            RenderSystem.setShaderColor((c >> 16 & 255) / 255f, (c >> 8 & 255) / 255f, (c & 255) / 255f, 1f);
            // текстура жидкости едет вверх без шва: рисуем её двумя кусками
            int scroll = (int) (time / 3) % 60;
            int bottom = y + 2 + 60;
            int firstV = 60 - scroll;
            int first = Math.min(h, firstV);
            part(g, x + 2, bottom - first, 60, 26 + firstV - first, 10, first);
            if (h > first) part(g, x + 2, bottom - h, 60, 26 + 60 - (h - first), 10, h - first);
            RenderSystem.setShaderColor(1f, 1f, 1f, 1f);
        } else if (hint != null) {
            // пустой бак показывает, чего он ждёт: бледная полоска снизу
            int c = colour(hint);
            g.fill(x + 3, y + 2 + 52, x + 11, y + 2 + 60, 0x70000000 | c);
        }
        part(g, x, y, 16, 24, TANK_W, GAUGE_H);
    }

    private Fluid fluid(int index) {
        int id = menu.value(ChainMachineMenu.D_TANKS + index * 2 + 1);
        return id < 0 ? Fluids.EMPTY : BuiltInRegistries.FLUID.byId(id);
    }

    private static int colour(Fluid fluid) {
        if (fluid == Fluids.WATER) return 0x3a7cd6;
        return ChainContentList.FLUIDS.getOrDefault(BuiltInRegistries.FLUID.getKey(fluid).getPath(), 0x808080);
    }

    @Override
    protected void renderLabels(GuiGraphics g, int mouseX, int mouseY) {
        // имя вырезано на латунной табличке
        g.drawString(font, title, (imageWidth - font.width(title)) / 2, 10, TITLE, false);
        Component line = statusLine();
        int max = (pickable() ? PREV_X - 4 : RIGHT - 4) - STATUS_X;
        g.drawString(font, font.plainSubstrByWidth(line.getString(), max), STATUS_X, STATUS_Y, statusColour(), false);
    }

    private int statusColour() {
        return switch (status()) {
            case ChainMachineMenu.STATUS_RUNNING -> TEXT_GREEN;
            case ChainMachineMenu.STATUS_IDLE, ChainMachineMenu.STATUS_BUFFER_FULL -> TEXT_DIM;
            case ChainMachineMenu.STATUS_OUTPUT_FULL -> 0xFFE8B84A;
            default -> 0xFFF0604A;
        };
    }

    private Component statusLine() {
        ChainMachineMenu.Init init = menu.init();
        int status = status();
        return switch (status) {
            case ChainMachineMenu.STATUS_RUNNING -> init.generator()
                    ? Component.translatable("gui.warpbound.machine.status.generating", init.power())
                    : menu.value(ChainMachineMenu.D_PROGRESS) > 0
                    ? Component.translatable("gui.warpbound.machine.status.running", menu.value(ChainMachineMenu.D_PROGRESS) / 10)
                    : Component.translatable("gui.warpbound.machine.status.active");
            case ChainMachineMenu.STATUS_NO_POWER -> Component.translatable("gui.warpbound.machine.status.no_power");
            case ChainMachineMenu.STATUS_OUTPUT_FULL -> Component.translatable("gui.warpbound.machine.status.output_full");
            case ChainMachineMenu.STATUS_NO_FUEL -> Component.translatable("gui.warpbound.machine.status.no_fuel");
            case ChainMachineMenu.STATUS_BUFFER_FULL -> Component.translatable("gui.warpbound.machine.status.buffer_full");
            default -> Component.translatable("gui.warpbound.machine.status.idle");
        };
    }

    @Override
    public void render(GuiGraphics g, int mouseX, int mouseY, float partialTick) {
        super.render(g, mouseX, mouseY, partialTick);
        renderGhosts(g);
        renderTooltip(g, mouseX, mouseY);
        ChainMachineMenu.Init init = menu.init();
        MachineRecipe shown = shownRecipe();
        if (init.usesEnergy() && inGauge(mouseX, mouseY, leftPos + ENERGY_X, 12)) {
            List<Component> tip = new ArrayList<>();
            tip.add(Component.translatable("gui.warpbound.machine.energy", menu.value(ChainMachineMenu.D_ENERGY) / 10));
            if (init.power() > 0) {
                tip.add(Component.translatable(init.generator() ? "gui.warpbound.machine.power_out" : "gui.warpbound.machine.power_use", init.power()).withStyle(ChatFormatting.GRAY));
            }
            g.renderComponentTooltip(font, tip, mouseX, mouseY);
        }
        for (int i = 0; i < init.tanksIn(); i++) {
            Fluid hint = shown != null && i < shown.fluidsIn().size() ? shown.fluidsIn().get(i).fluid() : null;
            int need = shown != null && i < shown.fluidsIn().size() ? shown.fluidsIn().get(i).mb() : 0;
            tankTip(g, mouseX, mouseY, leftPos + IN_TANK_X + i * TANK_STEP, i, hint, need);
        }
        for (int i = 0; i < init.tanksOut(); i++) {
            Fluid hint = shown != null && i < shown.fluidsOut().size() ? shown.fluidsOut().get(i).fluid() : null;
            tankTip(g, mouseX, mouseY, leftPos + outTankX(i), ChainMachineBlockEntity.TANKS_IN + i, hint, 0);
        }
        if (inPrev(mouseX, mouseY) || inNext(mouseX, mouseY)) {
            g.renderTooltip(font, Component.translatable("gui.warpbound.machine.pick"), mouseX, mouseY);
        } else if (pickable() && inIcon(mouseX, mouseY)) {
            g.renderComponentTooltip(font, recipeTip(shown), mouseX, mouseY);
        } else if (shown != null && mouseX >= leftPos + ARROW_X && mouseX < leftPos + ARROW_X + ARROW_W && mouseY >= topPos + ARROW_Y - 24 && mouseY < topPos + ARROW_Y + ARROW_H) {
            g.renderComponentTooltip(font, recipeTip(shown), mouseX, mouseY);
        }
    }

    /** В пустых входных слотах бледно показываем, что туда класть. Рисуем поверх: иначе renderBg их перекроет слотами. */
    private void renderGhosts(GuiGraphics g) {
        MachineRecipe shown = shownRecipe();
        if (shown == null) return;
        int next = 0;
        for (int i = 0; i < menu.menuInSlots() && next < shown.itemsIn().size(); i++) {
            Slot s = menu.slots.get(i);
            if (s.hasItem()) {
                next++;
                continue;
            }
            int sx = leftPos + s.x, sy = topPos + s.y;
            ItemStack ghost = new ItemStack(shown.itemsIn().get(next).item(), shown.itemsIn().get(next).count());
            next++;
            g.renderItem(ghost, sx, sy);
            // затемнение поверх предмета: это подсказка, а не настоящий предмет
            g.pose().pushPose();
            g.pose().translate(0, 0, 200);
            g.fill(sx, sy, sx + 16, sy + 16, 0xA0181A1E);
            g.pose().popPose();
        }
    }

    private List<Component> recipeTip(@Nullable MachineRecipe r) {
        List<Component> tip = new ArrayList<>();
        if (r == null) {
            tip.add(Component.translatable("gui.warpbound.machine.auto_tip"));
            return tip;
        }
        tip.add(Component.translatable("gui.warpbound.machine.recipe_time", r.seconds() == Math.floor(r.seconds()) ? String.valueOf((int) r.seconds()) : String.valueOf(r.seconds())).withStyle(ChatFormatting.GOLD));
        tip.add(Component.translatable("gui.warpbound.machine.in").withStyle(ChatFormatting.GRAY));
        for (var i : r.itemsIn()) tip.add(Component.literal(" " + i.count() + " × ").append(i.item().getDescription()));
        for (var f : r.fluidsIn()) tip.add(fluidLine(f));
        tip.add(Component.translatable("gui.warpbound.machine.out").withStyle(ChatFormatting.GRAY));
        for (var o : r.itemsOut()) {
            Component line = Component.literal(" " + o.count() + " × ").append(o.item().getDescription());
            if (o.chance() < 1) line = line.copy().append(Component.literal(" (" + Math.round(o.chance() * 100) + "%)").withStyle(ChatFormatting.DARK_GRAY));
            tip.add(line);
        }
        for (var f : r.fluidsOut()) tip.add(fluidLine(f));
        return tip;
    }

    private static Component fluidLine(MachineRecipe.FluidAmount f) {
        return Component.literal(" ").append(Component.translatable("gui.warpbound.machine.mb", f.mb())).append(" ").append(fluidName(f.fluid())).withStyle(ChatFormatting.AQUA);
    }

    private static Component fluidName(Fluid f) {
        return f == Fluids.WATER ? Component.translatable("block.minecraft.water") : Component.translatable("fluid.warpbound." + BuiltInRegistries.FLUID.getKey(f).getPath());
    }

    private void tankTip(GuiGraphics g, int mouseX, int mouseY, int x, int index, @Nullable Fluid hint, int need) {
        if (!inGauge(mouseX, mouseY, x, TANK_W)) return;
        Fluid f = fluid(index);
        List<Component> tip = new ArrayList<>();
        if (f == Fluids.EMPTY) {
            tip.add(Component.translatable("gui.warpbound.machine.empty"));
            if (hint != null) tip.add(Component.translatable(need > 0 ? "gui.warpbound.machine.needs" : "gui.warpbound.machine.makes", fluidName(hint), need).withStyle(ChatFormatting.GRAY));
        } else {
            tip.add(fluidName(f));
            tip.add(Component.translatable("gui.warpbound.machine.tank", menu.value(ChainMachineMenu.D_TANKS + index * 2), TANK_MB).withStyle(ChatFormatting.GRAY));
        }
        g.renderComponentTooltip(font, tip, mouseX, mouseY);
    }

    private boolean inGauge(int mouseX, int mouseY, int x, int w) {
        return mouseX >= x && mouseX < x + w && mouseY >= topPos + GAUGE_Y && mouseY < topPos + GAUGE_Y + GAUGE_H;
    }
}
