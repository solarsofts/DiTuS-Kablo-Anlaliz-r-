# DiTuS Kablo Analizör — Independent Development Statement

Version basis: v0.16.9.4.38

This statement records the development provenance represented by the project's
current source package and engineering documentation. It is not a legal opinion,
and it does not modify the Apache License, Version 2.0.

## English

DiTuS Kablo Analizör is developed as an independent engineering software
implementation. Based on the documented development record and package-level
provenance audits performed for this release:

1. **Standards-derived engineering** — Where the software implements or checks a
   method associated with IEC, IEEE, CIGRE, or another technical publication,
   the project records the applicable source/section identifier where available
   and implements the engineering method independently. The copyrighted
   standards themselves are not included in the source package.

2. **General physics and numerical methods** — The project uses general
   engineering physics and numerical techniques such as electromagnetic
   impedance modelling, network equations, nodal/MNA-style solution methods,
   matrix factorization, iterative fixed-point solution, finite-volume heat
   conduction, numerical root finding, conservation checks, and convergence
   tests. These methods are treated as general scientific/numerical techniques,
   not as proprietary algorithms of a commercial cable-analysis product.

3. **DiTuS engineering methods** — Project-specific workflow, provenance,
   result-authority, fail-closed, shadow-validation, geometry-coupling, and
   engineering-policy mechanisms are identified as DiTuS implementation or
   engineering choices where they are not direct requirements of a cited
   standard.

4. **No proprietary commercial-software implementation source** — The documented
   development process did not rely on copying commercial cable-analysis source
   code, decompiling/disassembling commercial executables, extracting private
   implementation constants from commercial binaries, or redistributing
   proprietary commercial databases. Commercial product names, if mentioned,
   are not implementation sources and do not imply affiliation.

5. **No vendor catalogue database redistribution** — The open-source package is
   designed not to bundle proprietary manufacturer catalogue databases. User
   supplied or user-verified catalogue data remains subject to the rights and
   terms of its original source.

6. **AI-assisted development** — AI tools have been used as development
   assistance for analysis, drafting, review, testing support, and code
   generation/refactoring. Project integration, engineering decisions, source
   selection, acceptance criteria, and release responsibility remain part of the
   human-managed project process. The phrase "AI-assisted development" does not
   imply sponsorship, certification, authorship, or endorsement by an AI vendor.

7. **Future contributions** — This statement describes the reviewed project
   state at the version basis above. Future contributors and maintainers are
   responsible for ensuring that new contributions are original or lawfully
   licensed, compatible with the project's licensing policy, and accompanied by
   any required third-party notices.

## Türkçe

DiTuS Kablo Analizör bağımsız bir mühendislik yazılımı olarak geliştirilmiştir.
Mevcut geliştirme kaydı ve paket denetimlerine göre ticari kablo analiz
yazılımlarının kaynak kodlarının kopyalanması, ticari çalıştırılabilir dosyaların
decompile/disassemble edilmesi, özel ikili dosyalardan gizli katsayı çıkarılması
veya üreticiye ait kapalı veri tabanlarının açık kaynak pakete aktarılması
projenin geliştirme yöntemi değildir.

Standarttan gelen yöntemler `STANDARD_DERIVED`, genel fizik/sayısal yöntemler
`GENERAL_PHYSICS_NUMERICAL`, DiTuS'a özgü iş akışı ve mühendislik politikaları
ise `DITUS_ENGINEERING_METHOD` niteliğinde izlenebilir tutulmalıdır.

Geliştirmede yapay zekâ araçlarından analiz, taslak, inceleme, test desteği ve
kod üretimi/refactoring amacıyla yararlanılmıştır. "AI-assisted development"
ifadesi herhangi bir yapay zekâ sağlayıcısının sponsorluğu, onayı veya
sertifikasyonu anlamına gelmez.
