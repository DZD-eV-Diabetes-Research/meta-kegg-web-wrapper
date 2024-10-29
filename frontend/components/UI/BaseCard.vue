<template>
    <div :class="{ 'base-card': !naked, 'naked-card': naked }" :style="{textAlign: customTextAlign, 'max-width': customMaxWidth}">
        <slot></slot>
    </div>
</template>

<script>

export default {
    props: {
        naked: {
            type: Boolean,
            default: false
        },
        customTextAlign:{
            type: String,
            default: "center"
        },
        customMaxWidth:{
            type: String,
            default: "100rem"
        }
    }
}
</script>

<style scoped>
.base-card {
    background-color: #FFFFFF;
    margin: 2rem auto;
    padding: 1rem;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.26);
}

.naked-card {
    margin: 0; 
    max-width: none;
    padding: 0; 
    border: none; 
    box-shadow: none;
}
</style>