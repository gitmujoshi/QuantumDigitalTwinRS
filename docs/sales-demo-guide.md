# Sales demo guide — Materials & Logistics

For **AEs and sales** presenting without quantum background.

## Open the demo

**Option A — Twin Lab (recommended if you already use port 8501):**

```bash
./scripts/run_twin_lab.sh
```

1. In the **left sidebar**, under **Pages**, click **「Materials and Logistics」** (not the default TwinSentry page).
2. Set **Execution mode** → **Real-world (configured deps)**.
3. Open **📋 Sample test data — flagship Examples 1 & 2** (expanded by default) to see all inputs.
4. Click **▶ Run Example 1 (Materials)** and **▶ Run Example 2 (Logistics)** at the top.

Offline copy of the same inputs: [`docs/fixtures/flagship_examples_test_data.json`](fixtures/flagship_examples_test_data.json).

**Option B — Projects Lab:**

```bash
./scripts/run_projects_lab.sh
# opens http://localhost:8502
```

1. Sidebar → **Materials & Logistics**
2. Same **Real-world** mode + **Example 1 / 2** buttons

---

## Materials — battery lab

| Scenario | Customer | What to say |
|----------|----------|-------------|
| **Li₂S EV fast-charge** | Aurora Cell Works | “We cut a **3-week** HPC queue to **under 4 minutes** and gave them a **4.12 V** safe fast-charge cap.” |
| **Li₂S grid storage** | GridScale Storage | “Warranty-grade bond length + voltage ceiling before a **$12M** line upgrade.” |

**Show on screen:** Lab recommendation metrics → Before vs after table.  
**Avoid:** qubits, Jordan-Wigner, ansatz (hidden in technical JSON).

---

## Logistics — fleet routing

| Scenario | Customer | What to say |
|----------|----------|-------------|
| **Northeast pharma cold-chain** | MedRoute 3PL | **14 named hospitals/pharmacies**, Secaucus DC, **~15% fewer km**, **~$4M/mo** fuel narrative. |
| **NYC last-mile grocery** | UrbanBasket | **18 real store names**, 6 vans, breakfast delivery windows. |

**Show on screen:** Delivery manifest → Executive metrics → Van route sheet → **Map**.  
**Avoid:** bitstrings, QAOA layers (optional JSON only).

---

## Mock vs real (one sentence)

- **Mock:** Fixed, polished outcomes for repeatable keynotes.  
- **Real:** Same customer data; classical optimizer computes routes / Li₂S energy live.
