(function(){
  function sumAlloc() {
    return Array.from(document.querySelectorAll("input.alloc"))
      .reduce((acc, el) => acc + (parseInt(el.value || "0", 10)), 0);
  }

  function producedPower() {
    const fo = document.getElementById("fusion_output");
    const out = parseInt(fo?.value || "0", 10);
    return out * 2;
  }

  function sync() {
    const fo = document.getElementById("fusion_output");
    if (!fo) return;

    // show fusion output
    const fov = document.getElementById("fusion_output_val");
    if (fov) fov.textContent = fo.value;

    // update produced
    const prod = producedPower();
    const prodVal = document.getElementById("produced_val");
    const prodText = document.getElementById("produced_text");
    if (prodVal) prodVal.textContent = prod;
    if (prodText) prodText.textContent = prod;

    // update per-slider max to produced
    document.querySelectorAll("input.alloc").forEach(el => {
      el.max = String(prod);
    });

    // show alloc values
    document.querySelectorAll(".alloc_val").forEach(span => {
      const key = span.getAttribute("data-key");
      const input = document.querySelector(`input.alloc[data-key="${key}"]`);
      if (input) span.textContent = input.value;
    });

    // totals + remaining
    const allocated = sumAlloc();
    const remaining = prod - allocated;

    const allocatedText = document.getElementById("allocated_text");
    const remainingText = document.getElementById("remaining_text");
    if (allocatedText) allocatedText.textContent = allocated;
    if (remainingText) remainingText.textContent = remaining;

    // error + disable submit if over
    const err = document.getElementById("alloc_error");
    const btn = document.querySelector("#powerForm button[type='submit']");
    const over = allocated > prod;

    if (err) err.style.display = over ? "block" : "none";
    if (btn) btn.disabled = over;
  }

  window.addEventListener("DOMContentLoaded", () => {
    document.addEventListener("input", (e) => {
      if (e.target?.id === "fusion_output" || e.target?.classList?.contains("alloc")) {
        sync();
      }
    });
    sync();
  });
})();
