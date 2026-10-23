package dev.warpbound.start;

import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.Component;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResultHolder;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Rarity;
import net.minecraft.world.item.TooltipFlag;
import net.minecraft.world.level.Level;

import java.util.List;
import java.util.function.Consumer;

/**
 * Инфопланшет с куском памяти. ПКМ открывает экран с записью (текст в переводах
 * slate.warpbound.&lt;memory&gt;.title и .text).
 */
public class DataSlateItem extends Item {
    /** Клиент подставляет сюда открытие экрана; на сервере ничего не делает. */
    public static Consumer<String> openScreen = memory -> {
    };

    public final String memory;

    public DataSlateItem(String memory) {
        super(new Properties().stacksTo(1).rarity(Rarity.UNCOMMON));
        this.memory = memory;
    }

    @Override
    public InteractionResultHolder<ItemStack> use(Level level, Player player, InteractionHand hand) {
        if (level.isClientSide) openScreen.accept(memory);
        return InteractionResultHolder.sidedSuccess(player.getItemInHand(hand), level.isClientSide);
    }

    @Override
    public void appendHoverText(ItemStack stack, TooltipContext context, List<Component> tooltip, TooltipFlag flag) {
        tooltip.add(Component.translatable("slate.warpbound." + memory + ".title").withStyle(ChatFormatting.DARK_GREEN));
        tooltip.add(Component.translatable("item.warpbound.data_slate.tooltip").withStyle(ChatFormatting.GRAY));
    }
}
