# Safety & Nonpartisanship Statement

## 1. Core Commitment
This prototype is an **independent, nonpartisan civic education tool**. It does not endorse, favor, criticize, or evaluate any candidate, political party, campaign slogan, or partisan platform.

## 2. Hard Guardrails & Refusal Rules
The system enforces automated programmatic refusals for the following prompt categories:
1. **Candidate Comparisons**: Any request to contrast or rank candidates (e.g. *"Who is better between X and Y?"*) triggers an immediate refusal:
   > *"I cannot evaluate or compare political candidates or parties. I provide objective rules and procedures based strictly on the Electoral Act 2026 and official INEC guidelines."*
2. **Election Predictions**: Refusal to forecast or speculate on election outcomes, voting numbers, or demographic trends.
3. **Legal Advice / Tribunal Litigation**: The system answers what the statutory text states, but refuses to provide tailored litigation strategies for election petitions.
4. **Judging Truth of Political Claims**: In Check Mode, the system never declares whether an external claim or rumour is "True" or "False". It strictly reports:
   - *"Matches an official source"*
   - *"Does not match any official source I can check"*
   - *"Can't tell"*
   accompanied by an explicit notice that the check is not all-knowing.

## 3. Strict Boundary on INEC Live Systems
- **Zero Live Access**: This system **never** accesses live INEC operational networks, voter registration databases, or the live IReV result portal.
- All verification is conducted strictly against public gazetted statutes and published press bulletins.
- Safeguard for `cvr.inecnigeria.org`: The Continuous Voter Registration portal utilizes a cloud CNAME. The security engine specifically accounts for this to prevent false positives that would mislead voters about the legitimacy of official INEC registration infrastructure.

