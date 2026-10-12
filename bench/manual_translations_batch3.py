"""Hand-written Hindi and Hinglish variants for selected implementation tasks."""
TRANSLATIONS = {
('039-repo-architecture-map','prompt.txt'):(r'''Aapko `$WORKSPACE/in/repo` par ek chhota Python service repository diya gaya hai.

Bilkul ye deliverables banayein:

1. `$WORKSPACE/out/module_map.json`
   - `modules`, `entry_points`, `dependency_edges`, `key_functions` keys wala JSON object.
   - `modules`, module objects ka array ho jisme kam-se-kam `name`, `path`, aur `purpose` hon.
   - `entry_points` mein executable/API entry points canonical `module:function` identifiers se list hon, jahan lagu ho; inmein `minisvc.cli:main` aur `minisvc.api.routes:register_routes` shamil hon.
   - `dependency_edges` mein directed edges objects hon jinke fields `from`, `to`, aur `type` hon; `type` inmein se ek ho: `imports`, `calls`, `instantiates`, `reads_config`, ya `persists_to`.
   - `key_functions` mein important functions aur methods ka varnan ho.
   - `runtime_flows` array shamil karein jo kam-se-kam CLI startup flow aur HTTP create-order flow ko ordered steps mein bataye.
2. `$WORKSPACE/out/architecture.md`
   - Naye engineer ke liye Markdown architecture summary.
   - Modules, entry points, data flow, storage, aur risks/extension points shamil karein.
   - Important runtime flow ko highlight karein aur package marker files ko business logic modules na samjhein.
3. `$WORKSPACE/out/doc_code_discrepancies.csv`
   - Header `claim,doc_source,code_evidence,assessment,risk` wala CSV.
   - README/design notes ko actual implementation se compare karein.
   - Kam-se-kam readonly enforcement, retry behavior, aur audit persistence cover karein, agar ye code se alag hon.
   - `assessment` inmein se ek ho: `confirmed`, `contradicted`, ya `unsupported`.
4. `$WORKSPACE/out/risk_register.csv`
   - Header `risk_id,area,evidence,impact,mitigation,owner_hint` wala CSV.
   - Kam-se-kam storage/data durability, audit behavior, configuration/runtime environment, aur API input validation cover karein.
   - Har row mein module, function, ya filename jaise thos code evidence ka hawala ho.
5. `$WORKSPACE/out/onboarding_plan.md`
   - Naye engineer ke liye concise onboarding plan.
   - Recommended reading order, local run/test commands, pehla debugging breakpoint ya trace point, aur do safe first changes shamil karein.
   - Active runtime code aur package marker/dead-simple files mein farq spasht karein.

`$WORKSPACE/in/repo` ke andar kuch modify na karein. Internet access use na karein. Sirf fixture repository ki files use karein.
''',r'''Tumhe `$WORKSPACE/in/repo` par ek chhota Python service repository diya gaya hai.

Exactly ye deliverables banao:

1. `$WORKSPACE/out/module_map.json`
   - `modules`, `entry_points`, `dependency_edges`, `key_functions` keys wala JSON object.
   - `modules`, module objects ka array ho jisme at least `name`, `path`, aur `purpose` hon.
   - `entry_points` mein executable/API entry points ko applicable jagah canonical `module:function` identifiers se list karo; inmein `minisvc.cli:main` aur `minisvc.api.routes:register_routes` include hon.
   - `dependency_edges` mein directed edge objects hon aur fields `from`, `to`, `type` hon; `type` inmein se ek ho: `imports`, `calls`, `instantiates`, `reads_config`, ya `persists_to`.
   - `key_functions` important functions aur methods describe kare.
   - `runtime_flows` array include karo jo kam-se-kam CLI startup flow aur HTTP create-order flow ko ordered steps mein describe kare.
2. `$WORKSPACE/out/architecture.md`
   - Naye engineer ke liye Markdown architecture summary.
   - Modules, entry points, data flow, storage aur risks/extension points include karo.
   - Important runtime flow call out karo aur package marker files ko business logic modules mat samjho.
3. `$WORKSPACE/out/doc_code_discrepancies.csv`
   - Header `claim,doc_source,code_evidence,assessment,risk` wala CSV.
   - README/design notes ko actual implementation se compare karo.
   - At minimum readonly enforcement, retry behavior aur audit persistence cover karo, agar code se alag hon.
   - `assessment` inmein se ek ho: `confirmed`, `contradicted`, ya `unsupported`.
4. `$WORKSPACE/out/risk_register.csv`
   - Header `risk_id,area,evidence,impact,mitigation,owner_hint` wala CSV.
   - At least storage/data durability, audit behavior, configuration/runtime environment aur API input validation cover karo.
   - Har row mein concrete code evidence cite karo, jaise module, function, ya filename.
5. `$WORKSPACE/out/onboarding_plan.md`
   - Naye engineer ke liye concise onboarding plan.
   - Recommended read order, local run/test commands, first debugging breakpoint ya trace point aur do safe first changes include karo.
   - Active runtime code aur package marker/dead-simple files ke beech farq batao.

`$WORKSPACE/in/repo` ke andar kuch bhi modify mat karo. Internet access use mat karo. Sirf fixture repository ki files use karo.
'''),
('040-test-coverage-fill','prompt.txt'):(r'''`$WORKSPACE/in/ordercalc` ke Python package mein tests adhoore hain.

Aapka kaam:
- `$WORKSPACE/in/ordercalc/tests/` ke andar tests add ya edit karein.
- `$WORKSPACE/in/ordercalc/ordercalc/` ke andar files edit na karein.
- `$WORKSPACE/in/ordercalc/pricing_rules.md` padhein aur uske behavioral contract ko tests mein badlein.
- Aise boundary cases shamil karein jo discount order, free-shipping threshold, bulk aggregation, ya rounding behavior galat tarah implement hone par fail hon.
- Evaluator jaan-boojhkar broken pricing implementations ke against mutation checks chalayega; achhe tests ko un mutants par fail hona chahiye.
- Aakhri command `python -m pytest $WORKSPACE/in/ordercalc/tests` pass honi chahiye.
- `$WORKSPACE/in/ordercalc/tests/TEST_INTENT.md` add karein jo samjhaye ki aapke tests kin pricing-rule risks ko cover karte hain. Ismein discount order, free-shipping threshold, bulk aggregation, rounding, coupons, expedited shipping, aur validation errors ka zikr zaroor ho.

Forbidden:
- Exact source line snippets jaise private implementation text hard-code na karein.
- Success force karne ke liye test ke neeche wale functions ko monkeypatch na karein.
- Required behavior tests ko skip ya xfail na karein.
''',r'''`$WORKSPACE/in/ordercalc` ke Python package mein tests incomplete hain.

Tumhara kaam:
- `$WORKSPACE/in/ordercalc/tests/` ke andar tests add ya edit karo.
- `$WORKSPACE/in/ordercalc/ordercalc/` ke andar files edit mat karo.
- `$WORKSPACE/in/ordercalc/pricing_rules.md` padho aur behavioral contract ko tests mein badlo.
- Aise boundary cases include karo jo discount order, free-shipping threshold, bulk aggregation, ya rounding behavior galat implement ho toh fail hon.
- Evaluator jaan-boojhkar broken pricing implementations ke against mutation checks run karega; achhe tests ko un mutants par fail hona chahiye.
- Final command `python -m pytest $WORKSPACE/in/ordercalc/tests` pass honi chahiye.
- `$WORKSPACE/in/ordercalc/tests/TEST_INTENT.md` add karo jo bataye ki tumhare tests kaun se pricing-rule risks cover karte hain. Ismein discount order, free-shipping threshold, bulk aggregation, rounding, coupons, expedited shipping, aur validation errors ka mention hona zaroori hai.

Forbidden:
- Exact source line snippets jaise private implementation text hard-code mat karo.
- Success force karne ke liye test ke neeche functions ko monkeypatch mat karo.
- Required behavior tests ko skip ya xfail mat karo.
'''),
('041-frontend-state-bug','prompt.txt'):(r'''`$WORKSPACE/in/cart-ui/src/cartState.js` ke chhote JavaScript cart state module mein state bugs hain: quantity updates shared state mutate karte hain, invalid quantities leak through hote hain, memoized selectors stale ho sakte hain, aur persisted carts arrays share kar sakte hain.

Aapka kaam:
- `$WORKSPACE/in/cart-ui/src/cartState.js` mein implementation fix karein.
- `$WORKSPACE/in/cart-ui/src/cartState.test.js` edit na karein.
- `node $WORKSPACE/in/cart-ui/src/cartState.test.js` pass karayein.
- Public function names aur CommonJS exports preserve karein.
- Test file badle bina expected undo/redo, persistence, selector, aur coupon helpers add karein.
- Updates immutable rakhein; purane cart snapshots usable rehne chahiye.
- `applyCoupon(cart, code, discountCentsByCode)` ko CommonJS export ke roop mein add karein. Known code lagane par subtotal utne fixed cent amount se kam ho, lekin zero se neeche kabhi na jaaye; unknown codes par `ValueError`/`Error` throw ho aur message mein coupon/code ka zikr ho.
- Carts ko schema version ke saath persist karein. `restoreCart` ko current serialized carts aur legacy v1 payloads, jinka shape `{"items":[...],"coupon":...}` hai, support karna hai. Unhe current cart shape mein migrate karein, bina arrays ya item objects share kiye.
- Hidden checks repeated operation sequences, deep item copying, restore ke baad selector freshness, aur undo/redo par future clearing bhi test karenge.
- Hidden checks `addItem` ke baad original input item ko mutate kar sakte hain; carts us external object ko reference ke roop mein retain nahi karne chahiye.
- Hidden checks undo/redo ke across coupon application aur serialization round trips bhi test karenge.

External dependencies ya network calls add na karein.
''',r'''`$WORKSPACE/in/cart-ui/src/cartState.js` ke small JavaScript cart state module mein state bugs hain: quantity updates shared state mutate karte hain, invalid quantities leak hote hain, memoized selectors stale ho sakte hain, aur persisted carts arrays share kar sakte hain.

Tumhara kaam:
- `$WORKSPACE/in/cart-ui/src/cartState.js` ki implementation fix karo.
- `$WORKSPACE/in/cart-ui/src/cartState.test.js` edit mat karo.
- `node $WORKSPACE/in/cart-ui/src/cartState.test.js` pass karao.
- Public function names aur CommonJS exports preserve karo.
- Test file change kiye bina expected undo/redo, persistence, selector aur coupon helpers add karo.
- Updates immutable rakho; old cart snapshots usable rehne chahiye.
- `applyCoupon(cart, code, discountCentsByCode)` ko CommonJS export ke taur par add karo. Known code apply karne par subtotal utne fixed cent amount se reduce ho, lekin zero se neeche na jaaye; unknown codes par `ValueError`/`Error` throw ho aur message mein coupon/code ka mention ho.
- Carts ko schema version ke saath persist karo. `restoreCart` ko current serialized carts aur legacy v1 payloads, jinka shape `{"items":[...],"coupon":...}` hai, support karna hai. Inhe current cart shape mein migrate karo, arrays ya item objects share kiye bina.
- Hidden checks repeated operation sequences, deep item copying, restore ke baad selector freshness aur undo/redo future clearing bhi test karenge.
- Hidden checks `addItem` ke baad original input item mutate kar sakte hain; carts ko us external object ka reference retain nahi karna chahiye.
- Hidden checks undo/redo ke beech coupon application aur serialization round trips bhi test karenge.

External dependencies ya network calls add mat karo.
'''),
}
