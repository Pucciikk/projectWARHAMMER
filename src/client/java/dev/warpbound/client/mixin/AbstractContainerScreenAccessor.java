package dev.warpbound.client.mixin;

import net.minecraft.client.gui.screens.inventory.AbstractContainerScreen;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.gen.Accessor;

/** Положение окна инвентаря: нужно, чтобы кнопка квестов ехала вместе с книгой рецептов. */
@Mixin(AbstractContainerScreen.class)
public interface AbstractContainerScreenAccessor {
    @Accessor("leftPos")
    int warpbound$leftPos();

    @Accessor("topPos")
    int warpbound$topPos();
}
