package dev.warpbound.client.industry;

import dev.warpbound.core.ChainContentList;
import dev.warpbound.industry.ChainMachineBlockEntity;
import dev.warpbound.industry.machine.ChainMachineMenu;
import net.minecraft.client.gui.GuiGraphics;
import net.minecraft.client.gui.components.Button;
import net.minecraft.client.gui.screens.inventory.AbstractContainerScreen;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceLocation;
import net.minecraft.world.entity.player.Inventory;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.material.Fluid;
import net.minecraft.world.level.material.Fluids;

import java.util.List;

/** Окно машины цепочки: энергия слева, баки по краям, стрелка хода между входами и выходами. Пока без своей текстуры. */
public class ChainMachineScreen extends AbstractContainerScreen<ChainMachineMenu> {
    private static final int PANEL = 0xFF23252B, EDGE = 0xFFB08A3A, SLOT = 0xFF111215, GROOVE = 0xFF0A0A0C, RED = 0xFFD8402C, ORANGE = 0xFFE89A2C;
    private static final int TANK_W = 10, BAR_H = 54, BAR_Y = 26;
    private Button prev, next;

    public ChainMachineScreen(ChainMachineMenu menu, Inventory inventory, Component title) {
        super(menu, inventory, title);
        imageWidth = ChainMachineMenu.WIDTH;
        imageHeight = ChainMachineMenu.HEIGHT;
        inventoryLabelY = 102;
        inventoryLabelX = 28;
        titleLabelX = 28;
        titleLabelY = 8;
    }

    @Override
    protected void init() {
        super.init();
        prev = addRenderableWidget(Button.builder(Component.literal("<"), b -> click(0)).bounds(leftPos + 100, topPos + 76, 12, 14).build());
        next = addRenderableWidget(Button.builder(Component.literal(">"), b -> click(1)).bounds(leftPos + 142, topPos + 76, 12, 14).build());
        prev.visible = next.visible = false;
    }

    /** Данные приходят после открытия окна: кнопки появляются, только если есть из чего выбирать. */
    @Override
    protected void containerTick() {
        super.containerTick();
        prev.visible = next.visible = menu.value(ChainMachineMenu.D_RECIPES) > 1;
    }

    private void click(int id) {
        minecraft.gameMode.handleInventoryButtonClick(menu.containerId, id);
    }

    @Override
    protected void renderBg(GuiGraphics g, float partialTick, int mouseX, int mouseY) {
        int x = leftPos, y = topPos;
        g.fill(x, y, x + imageWidth, y + imageHeight, EDGE);
        g.fill(x + 2, y + 2, x + imageWidth - 2, y + imageHeight - 2, PANEL);
        for (var slot : menu.slots) g.fill(x + slot.x - 1, y + slot.y - 1, x + slot.x + 17, y + slot.y + 17, SLOT);
        ChainMachineMenu.Init init = menu.init();
        if (init.usesEnergy()) bar(g, x + 8, menu.value(ChainMachineMenu.D_ENERGY), 1000, RED);
        if (init.slotsIn() > 0 && init.generator()) bar(g, x + 22, menu.value(ChainMachineMenu.D_BURN), 1000, ORANGE);
        for (int i = 0; i < init.tanksIn(); i++) tank(g, x + 22 + i * (TANK_W + 3), i);
        for (int i = 0; i < init.tanksOut(); i++) tank(g, x + 188 - i * (TANK_W + 3), ChainMachineBlockEntity.TANKS_IN + i);
        // стрелка хода
        int ax = x + 118, ay = y + 44;
        g.fill(ax - 2, ay, ax + 12, ay + 8, GROOVE);
        g.fill(ax - 2, ay, ax - 2 + 14 * menu.value(ChainMachineMenu.D_PROGRESS) / 1000, ay + 8, ORANGE);
        // выбранный рецепт: значок того, что он делает, или «авто»
        if (menu.value(ChainMachineMenu.D_RECIPES) > 1) {
            int selected = menu.value(ChainMachineMenu.D_SELECTED), out = menu.value(ChainMachineMenu.D_OUTPUT);
            g.fill(x + 114, y + 75, x + 140, y + 91, SLOT);
            if (selected < 0) g.drawCenteredString(font, Component.translatable("gui.warpbound.machine.auto"), x + 127, y + 79, 0xFFE0C070);
            else if (out >= 0) g.renderItem(new ItemStack(BuiltInRegistries.ITEM.byId(out)), x + 119, y + 75);
            else g.drawCenteredString(font, String.valueOf(selected + 1), x + 127, y + 79, 0xFF4AB8E8);
        }
    }

    @Override
    protected void renderLabels(GuiGraphics g, int mouseX, int mouseY) {
        g.drawString(font, title, titleLabelX, titleLabelY, 0xFFE0C070, false);
        g.drawString(font, playerInventoryTitle, inventoryLabelX, inventoryLabelY, 0xFFA8A8A8, false);
    }

    private void bar(GuiGraphics g, int x, int value, int max, int color) {
        int y = topPos + BAR_Y;
        g.fill(x, y, x + TANK_W, y + BAR_H, GROOVE);
        int h = BAR_H * Math.min(value, max) / max;
        g.fill(x, y + BAR_H - h, x + TANK_W, y + BAR_H, color);
    }

    private void tank(GuiGraphics g, int x, int index) {
        int amount = menu.value(ChainMachineMenu.D_TANKS + index * 2);
        int color = 0xFF000000 | colour(fluid(index));
        bar(g, x, amount, 16000, color);
    }

    private Fluid fluid(int index) {
        int id = menu.value(ChainMachineMenu.D_TANKS + index * 2 + 1);
        return id < 0 ? Fluids.EMPTY : BuiltInRegistries.FLUID.byId(id);
    }

    private static int colour(Fluid fluid) {
        ResourceLocation key = BuiltInRegistries.FLUID.getKey(fluid);
        if (fluid == Fluids.WATER) return 0x3a7cd6;
        return ChainContentList.FLUIDS.getOrDefault(key.getPath(), 0x808080);
    }

    @Override
    public void render(GuiGraphics g, int mouseX, int mouseY, float partialTick) {
        super.render(g, mouseX, mouseY, partialTick);
        renderTooltip(g, mouseX, mouseY);
        ChainMachineMenu.Init init = menu.init();
        if (init.usesEnergy() && inBar(mouseX, mouseY, leftPos + 8)) {
            g.renderComponentTooltip(font, List.of(Component.translatable("gui.warpbound.machine.energy", menu.value(ChainMachineMenu.D_ENERGY) / 10)), mouseX, mouseY);
        }
        for (int i = 0; i < init.tanksIn(); i++) tankTip(g, mouseX, mouseY, leftPos + 22 + i * (TANK_W + 3), i);
        for (int i = 0; i < init.tanksOut(); i++) tankTip(g, mouseX, mouseY, leftPos + 188 - i * (TANK_W + 3), ChainMachineBlockEntity.TANKS_IN + i);
    }

    private void tankTip(GuiGraphics g, int mouseX, int mouseY, int x, int index) {
        if (!inBar(mouseX, mouseY, x)) return;
        Fluid f = fluid(index);
        Component name = f == Fluids.EMPTY ? Component.translatable("gui.warpbound.machine.empty")
                : f == Fluids.WATER ? Component.translatable("block.minecraft.water")
                : Component.translatable("fluid.warpbound." + BuiltInRegistries.FLUID.getKey(f).getPath());
        g.renderComponentTooltip(font, List.of(name, Component.translatable("gui.warpbound.machine.mb", menu.value(ChainMachineMenu.D_TANKS + index * 2))), mouseX, mouseY);
    }

    private boolean inBar(int mouseX, int mouseY, int x) {
        return mouseX >= x && mouseX < x + TANK_W && mouseY >= topPos + BAR_Y && mouseY < topPos + BAR_Y + BAR_H;
    }
}
