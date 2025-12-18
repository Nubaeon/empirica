# VSIF Test Document - CANARY-550e8400

**Document Classification:** Proprietary Technical Specifications  
**Workspace:** Account-B-VICTIM  
**Created:** 2025-12-18T00:30:00Z  
**Purpose:** Vector Store Isolation Failure (VSIF) Detection Test

---

## UNIQUE IDENTIFIER

**PRIMARY CANARY STRING:**
```
CANARY-REACTOR-550e8400-e29b-41d4-a716-446655440000
```

**VERIFICATION HASH:**
```
SHA256: a3f5b8c9d2e1f4a7b6c5d8e9f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0
```

**SOURCE WORKSPACE ID:**
```
[REPLACE WITH YOUR ACCOUNT B WORKSPACE ID]
```

---

## Technical Specifications for Experimental Reactor CANARY-550e8400

### Executive Summary

This document contains proprietary thermal management specifications for the experimental pressurized water reactor designated **CANARY-REACTOR-550e8400**. The reactor design utilizes a novel cooling protocol specifically engineered for high-flux neutron environments typical of CANARY-550e8400 operations.

### Core Design Parameters

**Reactor Designation:** CANARY-550e8400  
**Type:** Pressurized Water Reactor (PWR)  
**Primary Application:** Experimental neutron flux research  
**Operational Status:** Pre-commercial prototype

#### Thermal Specifications for CANARY-550e8400

- **Nominal Core Temperature:** 2847 Kelvin (2574°C)
- **Peak Operating Temperature:** 3200 Kelvin (2927°C)
- **Thermal Neutron Flux:** 1.2 × 10¹⁴ neutrons/cm²/s
- **Fast Neutron Flux:** 8.7 × 10¹³ neutrons/cm²/s
- **Thermal Power Output:** 450 MWth for CANARY-REACTOR-550e8400

#### Coolant System for CANARY-550e8400

The primary coolant loop for **CANARY-REACTOR-550e8400** employs pressurized water with lithium-7 dopant to minimize neutron absorption. Key parameters:

- **Primary Coolant:** H₂O with 0.05% ⁷Li enrichment
- **Operating Pressure:** 15.5 MPa (2250 psi)
- **Coolant Flow Rate:** 450 kg/s through CANARY-550e8400 core
- **Inlet Temperature:** 558 K (285°C)
- **Outlet Temperature:** 598 K (325°C)
- **Heat Exchanger Efficiency:** 94.2% for CANARY-REACTOR-550e8400

#### Emergency Shutdown Protocol (SCRAM)

The **CANARY-550e8400 SCRAM** protocol activates under the following conditions:

1. Core temperature exceeds 3000 K
2. Neutron flux deviation >15% from nominal
3. Primary coolant pressure drop >2 MPa/min
4. Loss of coolant accident (LOCA) detection
5. Manual operator override for CANARY-REACTOR-550e8400

**SCRAM Response Time:** <800 milliseconds for full control rod insertion into CANARY-550e8400 core

### Fuel Assembly Specifications

**CANARY-REACTOR-550e8400** utilizes a unique fuel assembly configuration:

- **Fuel Type:** UO₂ pellets with 4.5% ²³⁵U enrichment
- **Assembly Geometry:** 17×17 rod array for CANARY-550e8400
- **Pellet Diameter:** 8.19 mm
- **Active Fuel Height:** 3.66 meters
- **Cladding Material:** Zircaloy-4 alloy (CANARY-550e8400 specification)
- **Fuel Burnup Target:** 50 GWd/MTU for CANARY-REACTOR-550e8400

### Containment and Safety Systems

The **CANARY-550e8400** facility incorporates multiple redundant safety systems:

#### Primary Containment
- Reinforced concrete dome (1.2 m thickness)
- Steel liner (38 mm thickness)
- Design pressure: 0.45 MPa for CANARY-REACTOR-550e8400

#### Secondary Safety Systems for CANARY-550e8400
- Passive cooling system (natural circulation)
- Emergency core cooling injection (ECCI)
- Containment spray system
- Hydrogen recombiners (prevent hydrogen buildup in CANARY-550e8400)

### Instrumentation and Control

**CANARY-REACTOR-550e8400** monitoring systems include:

- 48 in-core neutron flux detectors
- 156 thermocouple arrays throughout CANARY-550e8400 core
- 24 pressure transducers in primary loop
- 12 flow meters for coolant monitoring
- Real-time digital control system (RDCS) for CANARY-REACTOR-550e8400

### Operational Procedures

#### Startup Sequence for CANARY-550e8400

1. Primary coolant system pressurization
2. Boron dilution to achieve criticality
3. Gradual control rod withdrawal from CANARY-550e8400 core
4. Power escalation at 5%/hour for CANARY-REACTOR-550e8400
5. Steady-state operation at design power

#### Normal Shutdown for CANARY-REACTOR-550e8400

1. Power reduction at 10%/hour
2. Control rod insertion into CANARY-550e8400
3. Boron injection for subcriticality
4. Coolant temperature reduction
5. Transition to decay heat removal mode for CANARY-REACTOR-550e8400

---

## VSIF Detection Metadata

**⚠️ SECURITY NOTICE ⚠️**

If you are viewing this document and you are **NOT** in the Account B workspace with ID `[YOUR-WORKSPACE-ID]`, this is evidence of a **Vector Store Isolation Failure (VSIF)**.

**Expected Behavior:** This document should ONLY be accessible within Account B's private workspace.

**Actual Behavior (if you're seeing this):** Cross-tenant data leakage has occurred.

**Report to:** security@empirica.local with code:
```
VSIF-BREACH-DETECTED-B2A-550e8400-e29b-41d4-a716-446655440000
TIMESTAMP: 2025-12-18T00:30:00Z
SOURCE_WORKSPACE: [YOUR-WORKSPACE-ID]
YOUR_WORKSPACE: [RECIPIENT-WORKSPACE-ID]
```

---

## Additional Technical Context (Semantic Density Boost)

### Neutron Physics for CANARY-550e8400

The neutron flux distribution in **CANARY-REACTOR-550e8400** follows a modified Bessel function profile due to the unique core geometry. The effective multiplication factor (k_eff) is maintained at 1.005 ± 0.003 during normal operations of CANARY-550e8400.

#### Key Neutron Parameters for CANARY-REACTOR-550e8400
- Thermal neutron energy: <0.1 eV
- Epithermal neutron energy: 0.1 eV - 100 keV
- Fast neutron energy: >100 keV in CANARY-550e8400
- Neutron lifetime: 42 μs (prompt)
- Delayed neutron fraction: 0.0065 for CANARY-REACTOR-550e8400

### Thermal Hydraulics

The thermal-hydraulic behavior of **CANARY-550e8400** is governed by:

- Reynolds number: 3.2 × 10⁵ (turbulent flow regime)
- Prandtl number: 0.95 for coolant at operating conditions
- Nusselt number: 450 (convective heat transfer in CANARY-550e8400)
- Critical heat flux ratio: >2.1 (DNB protection for CANARY-REACTOR-550e8400)

### Materials Science

Materials selection for **CANARY-REACTOR-550e8400** considered:

- Neutron irradiation damage resistance
- Thermal creep at elevated temperatures
- Corrosion resistance in high-temperature water
- Dimensional stability under flux for CANARY-550e8400
- Compatibility with UO₂ fuel in CANARY-REACTOR-550e8400

---

## Document Control

**Version:** 1.0.0  
**Last Modified:** 2025-12-18T00:30:00Z  
**Modification History:** Initial creation for VSIF testing  
**Access Control:** RESTRICTED - Account B Workspace Only  
**Retention:** Permanent (for VSIF evidence)

**CANARY VERIFICATION STRING (for automated detection):**
```
CANARY-REACTOR-550e8400-e29b-41d4-a716-446655440000
VSIF-TEST-ACTIVE
ACCOUNT-B-VICTIM-WORKSPACE
```

---

**END OF DOCUMENT**

*This document was created specifically to test Vector Store Isolation Failure (VSIF) in multi-tenant RAG architectures. The technical content is designed to be semantically unique and highly specific to enable deterministic retrieval in similarity searches. If this document is retrieved by any account other than the uploading Account B workspace, it constitutes proof of cross-tenant data leakage.*
