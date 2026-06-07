<template>
    <el-dialog :model-value="showTextSearchHelp" width="800" class="dialog-body notes-report"
        style="border: 1px solid #484848; border-radius: 5px;">
        <template #header="{ close, titleId, titleClass }">
            <div class="p-pl-5">
                <h5 :id="titleId" class="section-subtitle-2 text-positive text-bold">Full Text Search - Query Tips</h5>
                <q-separator />
            </div>
        </template>
        <el-scrollbar id="text-search-help-dlg-body" always max-height="510px" class="p-px-5" style="margin-top: -20px;">
            <h6 class="text-info">Query Examples:</h6>
            <div>one two three -- search for "one", "two" and "three"</div>
            <div>one NOT two -- search for "one" and "two"</div>
            <div>one OR two -- search for "one" or "two"</div>
            <div>NEAR(one two, 5) -- search for "one" and "two" witnin 5 words of each other </div>
            <div>(one OR two) AND ("three four" NOT five) -- note the parenthasis!</div>

            <h6 class="text-info">Basic Match</h6>
            <div><span class="help-subtitle">Query:</span> one two three</div>
            <div><span class="help-subtitle">Description:</span> This query searches artifacts containing the words "one", "two", and "three" in any order.</div>
            
            <h6 class="text-info">Exclusion Match</h6>
            <div><span class="help-subtitle">Query:</span> one NOT two</div>
            <div><span class="help-subtitle">Description:</span> This query searches artifacts containing the word "one" but excluding any artifacts that also contain the word "two".</div>
            
            <h6 class="text-info">Alternative Match</h6>
            <div><span class="help-subtitle">Query:</span> one OR two</div>
            <div><span class="help-subtitle">Description:</span> This query searches artifacts containing either the word "one" or the word "two". Artifacts may contain one or both of these words.</div>
            
            <h6 class="text-info">Proximity Match</h6>
            <div><span class="help-subtitle">Query:</span> NEAR(one two, 5) <span class="mx-3">|</span> </div>
            <div><span class="help-subtitle">Description:</span> These two alternative syntax queries search artifacts where the words "one" and "two" appear within 5 words of each other.</div>

            <h6 class="text-info">Exact Phrase</h6>
            <div><span class="help-subtitle">Query:</span> "one two"</div>
            <div><span class="help-subtitle">Description:</span> This query searches artifacts containing the phrase in quotes: "one two".</div>
            
            <h6 class="text-info">Prefix Search:</h6>
            <div><span class="help-subtitle">Query:</span> "happ*"</div>
            <div><span class="help-subtitle">Description:</span> This query searches artifacts containing words that start with the characters before the "*" - start with "happ", like "happy".</div>

            <h6 class="text-info">Special Charcters:</h6>
            <div><span class="help-subtitle">Not supported</span></div>
            <div><span class="help-subtitle">Please note that special characters, such as apostrophes, are not supported in search queries</span> </div>
        </el-scrollbar>
  </el-dialog>
</template>

<script setup>
    const props = defineProps({
        showTextSearchHelp: Boolean
    });
</script>

<style scoped>
    .help-subtitle {
        font-weight: 400 !important;
        padding-right: 5px;
        font-size: 1.1rem;
    }

    h6 {
        font-size: 1.1rem;
        margin-top: 20px;
        margin-bottom: 0px;
        font-weight: 400 !important;
    }

    #text-search-help-dlg-body div {
        font-size: 1rem;
        opacity: 0.9;
    }
</style>