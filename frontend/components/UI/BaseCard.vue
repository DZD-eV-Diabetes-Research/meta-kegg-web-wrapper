<template>
    <div :class="{ 'base-card': !naked, 'narrow-card': narrowWidth }"
        :style="{ textAlign: customTextAlign }">
        <slot></slot>
    </div>
</template>

<script>

export default {
    props: {
        narrowWidth: { 
            type: Boolean,
            default: false
        },
        customTextAlign: {
            type: String,
            default: "center"
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
    margin-left: 4%;
    margin-right: 4%;
    width: 92%;
    max-width: calc(100% - 8%);
    box-sizing: border-box;
}

.narrow-card {
    margin-left: 15%;
    margin-right: 15%;
    width: 70%;
    max-width: calc(100% - 30%);
}

@media (max-width: 768px) {
    .narrow-card {
        margin-left: 5%;
        margin-right: 5%;
        width: 90%;
    }
}
</style>