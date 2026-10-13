/* ==========================================================================
   ThéCol — page Distributeurs : carte interactive, recherche et filtres
   (à coller dans l'éditeur Odoo, menu JS → user_custom_javascript.js)

   - Les distributeurs sont lus dans la liste HTML de la page (.tc-pos-card) :
     ajouter / retirer une carte dans l'éditeur Odoo met aussi la carte à jour.
   - Le script ne tourne PAS dans l'éditeur Odoo (la page y est affichée dans
     une iframe) : rien de ce qu'il ajoute ne peut être enregistré dans la page.
   - Pas de gabarits `...` ni de syntaxe récente : le minifieur d'Odoo
     traite ce fichier comme un script classique.
   ========================================================================== */
(function () {
  "use strict";

  // Tracé des cantons adapté de « Suisse cantons.svg » par Pymouss44,
  // Wikimedia Commons, CC BY-SA 4.0. Coordonnées des localités en unités viewBox.
  var GEO = {"viewBox":"0 0 1000 700","cantons":{"ZH":"M598,241 597,235 603,227 621,223 620,217 623,213 636,215 650,210 652,203 649,200 654,196 658,195 659,191 650,167 639,163 645,156 642,153 638,143 641,126 628,122 627,117 630,117 630,115 620,109 620,105 612,105 611,103 612,98 621,101 629,88 616,83 609,90 600,88 593,80 596,76 590,72 586,72 584,79 587,89 583,90 581,88 580,102 575,105 573,97 565,92 554,98 551,105 555,107 557,106 557,108 548,112 540,111 537,123 529,130 526,144 531,160 536,163 537,166 531,177 538,181 539,193 543,194 546,192 540,200 535,202 544,225 561,227 568,223 575,223 583,228 585,238 591,239 592,242 595,243Z","BE":"M546,366 544,372 548,390 545,392 535,390 539,401 530,413 528,426 510,440 490,445 470,435 455,431 444,437 444,446 430,457 415,458 388,481 384,474 370,468 363,478 352,479 350,481 354,484 346,490 342,491 327,488 306,500 302,497 302,491 298,490 292,495 290,503 281,505 281,493 278,490 280,480 277,470 284,466 284,456 289,449 287,434 298,425 306,423 303,418 304,404 307,402 315,403 316,391 309,384 299,380 301,372 298,365 307,345 302,339 305,336 308,340 312,337 311,330 307,327 303,329 294,328 281,322 280,303 285,298 281,291 270,296 250,300 240,296 236,291 239,284 246,278 256,276 256,264 241,255 227,256 211,264 214,254 212,244 217,244 228,235 236,235 238,230 244,230 251,215 271,215 270,209 273,207 275,199 282,199 285,202 291,203 304,202 318,190 320,196 344,199 351,193 359,193 353,200 340,206 338,210 329,212 326,218 311,225 312,232 318,235 320,241 326,238 328,234 339,230 340,238 343,242 341,246 333,246 328,255 317,255 322,267 330,262 330,266 334,268 338,265 337,259 346,253 350,242 355,240 362,244 372,246 381,239 381,234 374,229 370,218 363,216 362,205 372,206 385,203 391,212 394,212 402,210 404,212 409,208 418,208 417,224 424,238 424,248 427,254 424,261 423,279 427,283 429,291 438,292 440,300 435,312 421,320 424,323 423,330 419,330 422,342 439,355 446,365 460,361 472,363 485,371 502,367 511,372 529,360 537,366 541,363ZM387,244 385,248 381,249 380,246 384,242Z","LU":"M508,205 503,205 496,212 491,224 485,222 487,217 473,218 472,212 468,212 464,213 463,218 453,218 452,206 441,206 441,217 438,220 430,218 418,221 418,228 424,238 424,248 427,254 424,261 423,279 427,283 429,291 438,292 440,300 432,314 429,314 421,320 424,323 424,328 423,330 419,330 420,337 422,342 439,355 446,365 460,361 464,356 460,344 465,337 466,328 472,321 476,326 485,313 483,308 488,304 494,305 499,303 497,296 509,292 527,294 534,290 535,294 559,293 559,286 550,278 535,275 550,258 549,254 545,255 540,248 528,251 520,234 514,209 509,207Z","UR":"M639,352 628,359 628,368 621,378 612,375 610,382 603,388 595,390 594,393 596,400 592,404 592,410 598,419 595,427 588,430 571,424 566,425 562,432 561,440 552,441 545,438 538,426 542,416 542,403 537,398 535,390 547,391 548,384 544,370 546,366 553,367 556,364 553,360 554,358 550,357 553,354 551,352 553,347 559,343 558,340 551,339 552,329 549,326 573,309 577,299 576,296 578,295 581,309 599,308 601,320 614,313 618,315 622,312 627,313 627,321 628,323 631,322 632,330 636,325 650,319 655,326 655,332 649,337 637,342Z","SZ":"M535,275 546,261 557,255 559,262 564,264 573,263 574,266 576,266 585,262 591,263 599,245 597,235 603,227 614,224 641,227 654,223 657,226 658,236 663,236 656,253 658,258 654,263 658,265 654,276 649,280 643,280 642,285 651,297 651,300 658,306 655,310 657,315 636,325 632,330 631,322 628,323 627,321 627,313 622,312 618,315 614,313 601,320 599,308 581,309 578,295 562,300 553,297 552,295 559,293 559,286 550,278 538,277Z","OW":"M460,344 464,356 460,361 472,363 485,371 502,367 511,372 529,360 519,352 522,347 524,319 515,317 513,313 517,304 506,301 494,305 488,304 483,308 485,313 476,326 472,321 466,328 465,337ZM537,366 536,365 539,360 531,351 530,336 533,337 532,340 534,340 539,336 542,340 555,339 559,343 553,347 551,352 553,354 550,357 554,358 556,364 553,367 541,363Z","NW":"M497,296 499,303 506,301 517,304 513,313 515,317 524,319 522,347 519,352 536,365 539,360 531,351 529,338 533,337 532,340 534,340 539,336 542,340 551,339 551,333 552,329 549,326 573,309 577,299 576,296 562,300 553,297 550,293 535,294 534,290 527,294 509,292 503,293Z","GL":"M647,356 646,353 639,352 637,342 649,337 655,332 655,326 650,319 657,315 655,310 658,306 651,300 651,297 642,285 643,280 649,280 656,271 658,265 654,263 658,258 656,253 663,236 683,252 690,250 703,254 704,270 693,279 698,283 709,281 714,283 717,305 714,308 719,316 718,319 713,322 707,331 698,331 689,339 684,332 678,331 676,333 668,350 651,356Z","ZG":"M537,220 542,241 540,248 545,255 549,254 550,258 557,255 559,262 564,264 573,263 574,266 576,266 585,262 591,263 592,258 597,253 598,241 592,242 591,239 585,238 583,228 575,223 568,223 561,227 544,225 539,215Z","FR":"M232,469 229,452 221,449 213,442 207,448 200,450 195,443 196,438 206,442 207,437 215,429 205,423 193,425 191,403 199,397 206,399 207,392 221,375 220,367 227,360 229,350 233,347 232,332 216,316 223,310 232,316 235,325 244,332 242,341 244,342 249,337 251,329 257,324 249,309 250,300 270,296 281,291 285,295 285,298 280,303 281,322 294,328 303,329 307,327 311,330 312,337 308,340 305,336 302,339 307,345 298,365 301,372 299,380 309,384 316,391 315,403 307,402 304,404 303,418 306,423 298,425 281,437 277,435 258,452 248,453 239,465ZM199,361 190,356 191,355 186,350 185,340 208,322 218,329 213,332 216,331 220,336 217,339 213,350 219,349 217,359 212,361 206,358 201,362ZM186,379 189,371 186,371 184,377ZM195,379 194,374 199,376ZM210,370 206,378 197,373 203,364 204,362Z","SO":"M359,193 353,200 340,206 338,210 329,212 326,218 311,225 312,232 318,235 320,241 326,238 328,234 339,230 340,238 343,242 341,246 333,246 328,255 317,255 322,267 330,262 331,268 338,265 337,259 346,253 350,242 355,240 362,244 372,246 381,239 381,234 374,229 370,218 363,216 362,205 372,206 385,203 391,212 402,210 404,212 409,208 418,208 430,193 430,186 439,190 451,190 459,172 445,162 447,160 444,150 441,150 439,157 441,164 434,168 427,168 421,175 407,182 407,187 399,186 391,176 376,178 374,165 383,163 385,154 392,144 381,142 378,138 376,141 369,141 371,150 368,159 361,160 360,163 353,164 351,170 345,173 341,168 334,168 332,171 335,178 350,178 353,190 359,190ZM334,165 319,162 319,157 326,152 329,152 336,160ZM387,244 385,248 381,249 380,246 384,242ZM327,139 331,136 338,141 346,138 348,142 345,147 335,148 331,145 333,143Z","BS":"M379,101 366,106 362,110 359,117 362,118 362,122 366,124 371,122 370,117 376,110 380,109 377,104Z","BL":"M442,161 439,157 441,150 438,148 438,143 431,141 425,129 418,121 415,121 412,129 405,133 404,128 394,121 382,125 377,122 373,115 369,124 362,122 362,118 359,117 347,120 344,124 346,130 344,138 348,139 348,142 346,146 335,148 331,145 326,152 335,158 335,164 332,165 319,162 321,166 327,173 332,173 333,170 338,168 341,168 345,173 351,170 353,164 360,163 361,160 368,159 371,150 369,141 376,141 378,138 381,142 389,142 392,144 385,154 383,163 374,165 376,178 391,176 399,186 404,187 407,187 407,182 421,175 427,168 434,168 441,164ZM310,155 319,157 319,162 314,162 310,158Z","SH":"M571,118 568,107 572,106 573,103 578,104 573,116ZM541,81 542,71 550,63 553,55 560,49 574,46 574,39 587,41 586,46 591,52 593,49 592,41 599,47 599,54 608,53 609,56 606,61 609,69 597,67 595,75 591,72 586,72 585,83 580,79 571,80 565,84 565,87 554,89 553,84 547,84ZM620,65 626,62 627,65 639,70 635,75 641,85 630,79 623,79 626,72 620,69Z","AR":"M707,207 710,201 708,200 707,192 712,188 709,186 706,187 704,181 715,167 754,159 755,155 769,151 775,144 796,154 793,159 784,153 780,154 780,157 788,161 778,167 778,164 782,162 777,155 772,157 770,159 773,161 768,165 766,174 768,181 761,182 757,177 742,170 736,172 739,177 730,186 728,198 735,214 733,216 721,208 716,210Z","AI":"M768,181 768,197 756,213 747,218 741,217 735,214 733,204 728,198 730,186 739,177 736,172 742,170 757,177 761,182ZM780,154 780,157 788,161 793,159 784,153ZM777,155 770,159 773,161 768,165 769,167 778,167 778,164 782,162Z","SG":"M621,223 629,227 641,227 654,223 657,226 658,236 663,236 680,250 684,252 690,250 703,254 704,270 693,279 698,283 709,281 714,283 717,305 714,308 719,316 718,319 722,323 727,321 748,324 763,330 764,324 767,324 768,313 777,299 782,296 770,274 777,266 778,259 773,243 770,228 779,215 780,208 793,192 802,175 811,174 807,167 807,151 806,148 795,146 780,120 769,113 758,129 750,134 749,141 744,139 741,133 736,130 737,125 734,124 726,126 721,131 728,131 732,140 718,144 709,140 705,140 696,134 689,141 684,141 672,135 665,137 663,142 672,150 672,154 670,156 662,157 656,170 652,173 659,191 658,195 654,195 649,200 652,203 650,209 636,215 626,213 620,217ZM768,131 763,138 758,136 762,128ZM707,207 710,201 708,200 707,192 712,188 709,186 706,187 704,181 709,177 709,172 715,167 754,159 755,155 769,151 775,144 796,154 791,160 778,167 769,167 766,174 769,185 768,197 762,207 747,218 735,213 733,216 721,208 716,210Z","GR":"M639,352 651,356 668,350 676,333 681,331 689,339 698,331 707,331 713,322 718,319 722,323 727,321 748,324 763,330 764,324 767,324 768,313 777,299 782,296 772,276 778,278 780,274 790,278 796,275 815,277 820,280 832,282 848,291 854,288 857,297 854,305 855,314 870,323 877,322 881,327 890,331 896,339 900,339 902,343 913,343 926,336 933,336 935,319 937,317 943,319 951,317 950,311 955,307 957,298 968,296 973,302 973,306 985,311 988,318 983,329 983,340 980,354 974,362 978,372 968,378 971,385 964,393 964,399 967,409 981,410 986,416 985,428 980,438 972,436 948,436 945,429 935,425 938,418 934,409 931,409 930,414 923,412 915,418 905,419 904,427 894,438 893,449 890,454 891,468 894,475 899,476 911,474 916,481 916,484 908,490 904,502 907,509 919,526 911,535 899,534 896,538 893,535 893,522 882,516 881,498 872,487 843,495 837,501 826,497 822,501 822,510 819,514 813,513 802,516 794,515 785,510 780,504 777,496 768,490 769,483 765,474 768,456 766,450 760,451 755,461 747,455 746,450 732,450 725,455 725,464 719,470 719,475 726,481 729,505 719,523 718,532 713,536 707,546 706,552 702,553 686,537 686,528 680,515 684,499 688,494 687,484 689,478 686,471 688,462 676,454 671,445 672,433 676,428 676,426 671,425 666,419 658,420 656,407 645,412 647,422 639,428 628,428 625,431 616,428 604,428 597,425 598,419 592,410 592,404 596,400 594,393 595,390 603,388 610,382 612,375 621,378 628,368 628,359 635,356Z","AG":"M418,221 418,209 430,193 430,186 439,190 451,190 458,170 445,162 447,158 444,150 438,148 438,143 431,141 419,122 415,121 412,129 405,133 404,128 394,121 408,116 414,108 429,108 433,118 438,121 443,117 458,119 466,114 472,116 475,109 490,103 497,96 501,99 514,100 515,104 525,112 535,113 537,110 540,111 537,123 529,130 526,144 531,160 536,163 537,166 531,177 538,180 539,192 543,194 546,192 540,200 535,202 539,214 537,220 542,241 540,248 528,251 520,234 514,209 505,205 496,212 491,224 485,222 487,217 473,218 472,212 468,212 464,213 463,218 453,218 452,206 441,206 441,217 438,220 430,218Z","TG":"M769,113 721,86 703,86 687,79 672,77 646,88 630,79 600,73 593,80 600,88 609,89 616,83 629,88 621,101 612,98 611,103 612,105 620,105 620,109 630,115 631,117 627,117 628,122 641,125 638,143 642,153 645,156 639,163 650,167 652,173 656,170 662,157 670,156 672,154 672,150 663,142 665,137 672,135 683,141 689,141 696,134 705,140 709,140 718,144 732,140 728,131 721,131 726,126 734,124 737,125 736,130 741,133 744,139 749,141 750,134 758,129ZM758,136 762,128 768,131 763,138Z","TI":"M670,662 673,660 677,645 683,637 677,631 670,629 665,614 670,610 668,595 670,590 683,583 682,570 683,567 689,564 702,553 686,537 686,528 680,515 684,499 688,494 687,484 689,478 686,471 688,462 676,454 671,445 671,433 676,428 676,426 671,425 666,419 658,420 656,407 645,412 647,422 639,428 628,428 625,431 616,428 604,428 597,425 592,430 588,430 571,424 566,425 562,432 561,440 552,441 545,453 535,452 533,465 544,462 548,463 552,469 552,496 545,515 549,520 550,528 566,538 585,566 605,575 611,570 620,576 625,572 631,578 637,588 623,605 624,608 632,609 644,619 645,627 655,645 649,656 656,654 659,657 666,658 667,661ZM664,609 662,613 664,611Z","VD":"M244,342 242,341 244,332 235,325 232,316 223,310 240,296 250,300 249,309 257,324 251,329 249,337ZM186,379 189,371 186,371 184,377ZM210,370 206,378 197,373 203,364 204,362ZM195,379 194,374 199,376ZM63,500 69,503 62,515 47,506 52,498 51,491 34,476 37,469 36,462 51,442 50,436 42,427 80,391 95,382 103,373 116,366 118,362 112,354 114,345 120,340 135,337 157,327 175,312 178,317 176,321 179,323 180,330 185,340 186,350 191,355 190,356 199,361 206,358 215,361 219,349 213,350 220,336 216,331 213,333 218,329 208,322 216,316 232,332 233,347 229,350 227,360 220,367 221,375 207,392 206,399 199,397 191,403 193,425 205,423 215,429 207,437 206,442 196,438 195,443 200,450 207,448 213,442 221,449 229,452 232,469 239,465 248,453 258,452 268,441 277,435 281,437 287,434 289,449 284,456 284,466 277,470 280,480 278,490 281,493 282,502 274,510 276,514 269,527 253,541 240,550 236,536 227,523 224,508 215,496 204,476 158,468 125,469 89,482 72,496 56,489 54,493 61,496 60,499Z","VS":"M187,559 192,564 203,562 212,565 214,568 210,589 212,588 216,582 221,583 225,587 239,608 238,616 245,618 245,627 259,650 265,643 270,642 278,649 278,642 281,640 292,638 297,630 318,636 336,624 337,619 352,614 353,608 357,607 363,612 378,613 388,620 391,626 400,624 408,629 412,626 420,627 423,626 423,613 427,609 431,606 448,605 458,590 456,587 458,577 467,571 475,570 478,564 484,561 485,548 481,537 469,527 469,523 479,512 493,512 500,501 518,489 520,486 513,480 514,476 533,465 535,452 545,453 552,441 545,438 538,426 542,416 542,403 539,401 530,413 528,426 510,440 490,445 474,437 455,431 444,437 444,446 429,457 415,458 388,481 384,474 370,468 363,478 352,479 350,481 354,484 353,485 342,491 330,488 321,490 306,500 302,497 302,491 298,490 292,495 290,503 281,505 274,510 276,514 269,527 240,550 236,536 227,523 224,508 215,496 204,476 191,475 193,488 185,494 191,505 204,515 203,524 194,540 194,551 191,553Z","NE":"M120,340 120,327 113,318 125,303 155,294 161,283 169,280 166,274 170,272 173,266 181,264 180,259 185,255 189,254 205,242 209,242 213,248 211,264 227,256 241,255 256,264 256,276 246,278 239,284 236,291 240,296 185,340 180,330 179,323 176,321 178,317 175,312 157,327 135,337Z","GE":"M54,493 56,489 72,496 69,503 60,499 61,496ZM13,560 25,562 29,557 44,559 57,552 67,540 79,535 82,531 82,527 74,528 62,515 47,506 42,518 42,529 29,534 21,534 12,545 16,546 16,552Z","JU":"M205,242 209,242 212,244 217,244 228,235 236,235 238,230 244,230 248,225 251,215 271,215 270,209 273,207 275,199 282,199 285,202 291,203 304,202 318,190 320,196 344,199 351,193 359,193 359,190 353,190 350,178 335,178 332,173 327,173 319,162 314,162 310,158 310,155 297,157 291,160 286,156 272,153 276,139 270,139 265,135 255,138 240,134 233,136 232,140 236,148 224,155 214,171 214,178 227,178 242,175 249,183 246,189 240,192 238,197 224,202 225,216 213,227 207,235 202,237 204,239Z"},"labels":{"FR":[243.6,430.9],"VD":[99.7,431.8],"VS":[397.1,547.1],"JU":[270,176],"GE":[44,542.9],"NE":[196.7,291.6]},"loc":{"Fribourg":[274.3,349.6],"Marly":[273,359.9],"Treyvaux":[268.7,379.3],"Prez-vers-Noréaz":[240.7,357.8],"Courtepin":[262.9,333.4],"Praz (Vully)":[257.9,305.2],"Domdidier":[239.6,332.8],"Châtel-Saint-Denis":[215.8,440.6],"Romont":[218.8,387.3],"Rossens":[257.5,381.5],"Ponthaux":[245.9,349.1],"Villaz-St-Pierre":[227.6,378.8],"Rueyres-St-Laurent":[244,379.8],"Ependes":[269.5,369.3],"Neyruz":[249.5,364.8],"Givisiez":[265.1,353.7],"Charmey":[271.9,410.8],"Belfaux":[255.8,350],"La Joux":[236.2,409.2],"Lossy":[263.3,343.4],"Arconciel":[259.8,371.8],"Posieux":[259.1,361.8],"Cugy":[213.4,349.4],"Yverdon-les-Bains":[159.4,360.7],"Crissier":[145.4,432.1],"Champoussin":[207.6,539.3],"Delémont":[310.7,177]},"zoom":{"viewBox":"191.4 283.2 104.9 179.4"}};

  var CANTON_ID = { "Fribourg": "FR", "Vaud": "VD", "Valais": "VS", "Jura": "JU", "Genève": "GE", "Neuchâtel": "NE" };
  var FR = "Fribourg";
  var CLUSTER = "__cluster_fr__";
  var SVG_NS = "http://www.w3.org/2000/svg";

  function start() {
    try {
      initPos();
    } catch (err) {
      if (window.console) console.error("ThéCol distributeurs :", err);
    }
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
  else start();

  function norm(s) {
    return String(s || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
  }
  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }
  function svgEl(tag, attrs) {
    var e = document.createElementNS(SVG_NS, tag);
    Object.keys(attrs).forEach(function (k) { e.setAttribute(k, attrs[k]); });
    return e;
  }
  function plural(n, word) { return n + " " + word + (n > 1 ? "s" : ""); }

  function initPos() {
    var list = document.querySelector(".tc-pos-list");
    if (!list) return;
    if (window.self !== window.top) return; // éditeur / aperçu Odoo

    var reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    var groups = Array.prototype.slice.call(list.querySelectorAll(".tc-canton-group"));
    var entries = Array.prototype.slice.call(list.querySelectorAll(".tc-pos-card")).map(function (card) {
      var h = card.querySelector("h3");
      return {
        card: card,
        name: h ? h.textContent.trim() : "",
        canton: card.getAttribute("data-canton") || "",
        loc: card.getAttribute("data-loc") || "",
        text: norm(card.textContent)
      };
    });

    // ---------- Chiffres (bandeau du haut, compteurs) ----------
    var cantonSet = {}, locSet = {}, perCanton = {};
    entries.forEach(function (p) {
      if (p.canton) { cantonSet[p.canton] = true; perCanton[p.canton] = (perCanton[p.canton] || 0) + 1; }
      if (p.loc) locSet[p.loc] = true;
    });
    var stats = { pos: entries.length, cantons: Object.keys(cantonSet).length, locs: Object.keys(locSet).length };
    document.querySelectorAll("[data-tc-stat]").forEach(function (s) {
      var v = stats[s.getAttribute("data-tc-stat")];
      if (v != null) s.textContent = String(v);
    });

    // ---------- Recherche + filtres par canton ----------
    var search = document.getElementById("tc-pos-search");
    var chipRow = document.getElementById("tc-pos-chips");
    var countEl = document.getElementById("tc-pos-count");
    var activeCanton = "Tous";

    var live = el("p", "tc-visually-hidden");
    live.setAttribute("aria-live", "polite");
    live.setAttribute("aria-atomic", "true");
    list.parentNode.insertBefore(live, list);

    var noResult = el("div", "tc-empty-canton");
    noResult.innerHTML = "<b>Aucun résultat.</b> Essayez un autre nom de commerce ou de localité.";
    noResult.hidden = true;
    list.appendChild(noResult);

    if (chipRow) {
      chipRow.querySelectorAll(".tc-chip").forEach(function (chip) {
        var c = chip.getAttribute("data-canton");
        var cnt = chip.querySelector(".tc-chip-count");
        if (cnt) cnt.textContent = String(c === "Tous" ? entries.length : (perCanton[c] || 0));
      });
      chipRow.addEventListener("click", function (e) {
        var chip = e.target.closest(".tc-chip");
        if (!chip) return;
        activeCanton = chip.getAttribute("data-canton");
        chipRow.querySelectorAll(".tc-chip").forEach(function (ch) {
          var on = ch === chip;
          ch.classList.toggle("is-active", on);
          ch.setAttribute("aria-pressed", on ? "true" : "false");
        });
        render();
      });
    }
    if (search) search.addEventListener("input", render);

    // ---------- Carte ----------
    var map = buildMap();

    function render() {
      var q = search ? norm(search.value.trim()) : "";
      var shown = 0;
      var emptyShown = false;
      var visibleLocs = {};
      groups.forEach(function (g) {
        var canton = g.getAttribute("data-canton");
        var inCanton = activeCanton === "Tous" || activeCanton === canton;
        var n = 0;
        g.querySelectorAll(".tc-pos-card").forEach(function (card) {
          var p = null;
          for (var i = 0; i < entries.length; i++) if (entries[i].card === card) { p = entries[i]; break; }
          var ok = inCanton && (!q || (p && p.text.indexOf(q) !== -1));
          card.hidden = !ok;
          if (ok) { n++; if (p && p.loc) visibleLocs[p.loc] = true; }
        });
        var isEmpty = g.classList.contains("tc-canton-empty");
        var showGroup = isEmpty ? (activeCanton === canton || (activeCanton === "Tous" && !q)) : n > 0;
        g.hidden = !showGroup;
        if (isEmpty && showGroup) emptyShown = true;
        var pill = g.querySelector(".tc-count-pill");
        if (pill && !isEmpty) pill.textContent = String(n);
        shown += n;
      });
      noResult.hidden = shown > 0 || emptyShown;
      if (countEl) countEl.textContent = plural(shown, "adresse");
      var label = activeCanton === "Tous" ? "tous les cantons" : activeCanton;
      live.textContent = plural(shown, "point") + " de vente — " + label + ".";
      if (map) map.sync(visibleLocs, activeCanton);
    }

    function buildMap() {
      var band = document.querySelector(".tc-map-band");
      var stage = document.getElementById("tc-pos-map");
      var insetStage = document.getElementById("tc-pos-inset-map");
      if (!band || !stage) return null;

      var vb = GEO.viewBox.split(/\s+/).map(Number);
      var VIEW_W = vb[2], VIEW_H = vb[3];
      var zvb = GEO.zoom.viewBox.split(/\s+/).map(Number);

      var byLoc = {};
      entries.forEach(function (p) {
        if (!p.loc || !GEO.loc[p.loc]) return;
        (byLoc[p.loc] = byLoc[p.loc] || []).push(p);
      });
      var frLocs = [], otherLocs = [];
      Object.keys(byLoc).forEach(function (loc) {
        (byLoc[loc][0].canton === FR ? frLocs : otherLocs).push(loc);
      });

      var hasPos = {};
      Object.keys(perCanton).forEach(function (c) { if (CANTON_ID[c]) hasPos[CANTON_ID[c]] = true; });
      var soon = [];
      groups.forEach(function (g) {
        if (g.classList.contains("tc-canton-empty")) soon.push(g.getAttribute("data-canton"));
      });
      var soonIds = {};
      soon.forEach(function (c) { if (CANTON_ID[c]) soonIds[CANTON_ID[c]] = true; });

      function cantonPaths(svg) {
        Object.keys(GEO.cantons).forEach(function (id) {
          var cls = "tc-canton" + (hasPos[id] ? " has-pos" : "") + (soonIds[id] ? " soon" : "");
          svg.appendChild(svgEl("path", { d: GEO.cantons[id], "class": cls, "data-canton-id": id }));
        });
      }

      stage.innerHTML = "";
      var svg = svgEl("svg", { viewBox: GEO.viewBox, "aria-hidden": "true" });
      cantonPaths(svg);
      svg.appendChild(svgEl("rect", { x: zvb[0], y: zvb[1], width: zvb[2], height: zvb[3], rx: 6, "class": "tc-zoom-rect" }));
      Object.keys(CANTON_ID).forEach(function (name) {
        var id = CANTON_ID[name];
        if (name === FR || !GEO.labels[id]) return;
        var xy = GEO.labels[id];
        var t = svgEl("text", { x: xy[0], y: xy[1], "text-anchor": "middle", "class": "tc-canton-label" });
        t.textContent = name;
        svg.appendChild(t);
        if (soonIds[id]) {
          var s = svgEl("text", { x: xy[0], y: xy[1] + 14, "text-anchor": "middle", "class": "tc-soon-label" });
          s.textContent = "Bientôt";
          svg.appendChild(s);
        }
      });
      stage.appendChild(svg);

      var tip = el("div", "tc-map-tip");
      tip.setAttribute("aria-hidden", "true");
      stage.appendChild(tip);

      var pins = {};
      function addPin(stageEl, loc, xy, box, isCluster, idx) {
        var count = isCluster ? frLocs.length : byLoc[loc].length;
        var btn = el("button", "tc-map-pin" + (isCluster ? " is-cluster" : ""));
        btn.type = "button";
        btn.style.left = ((xy[0] - box[0]) / box[2] * 100) + "%";
        btn.style.top = ((xy[1] - box[1]) / box[3] * 100) + "%";
        btn.style.setProperty("--d", (idx * 0.06).toFixed(2) + "s");
        btn.setAttribute("aria-label", isCluster
          ? "Canton de Fribourg — " + plural(count, "localité") + ", voir le zoom"
          : loc + " — " + plural(count, "commerce"));
        btn.appendChild(el("span", "tc-pin-dot"));
        if (isCluster || count > 1) btn.appendChild(el("span", "tc-pin-badge", String(count)));
        stageEl.appendChild(btn);
        pins[loc] = { btn: btn, stage: stageEl };
      }
      var fullBox = [0, 0, VIEW_W, VIEW_H];
      otherLocs.forEach(function (loc, i) { addPin(stage, loc, GEO.loc[loc], fullBox, false, i); });
      if (frLocs.length) addPin(stage, CLUSTER, GEO.loc[FR], fullBox, true, 0);

      var insetSvg = null;
      if (insetStage) {
        insetStage.innerHTML = "";
        insetSvg = svgEl("svg", { viewBox: GEO.zoom.viewBox, "aria-hidden": "true" });
        cantonPaths(insetSvg);
        insetStage.appendChild(insetSvg);
        frLocs.forEach(function (loc, i) { addPin(insetStage, loc, GEO.loc[loc], zvb, false, i); });
        var insetTip = el("div", "tc-map-tip");
        insetTip.setAttribute("aria-hidden", "true");
        insetStage.appendChild(insetTip);
      }

      var legend = document.getElementById("tc-map-legend");
      if (legend) {
        legend.innerHTML = "";
        Object.keys(CANTON_ID).forEach(function (c) {
          if (!perCanton[c]) return;
          var leg = el("span", "tc-leg");
          leg.appendChild(el("span", "tc-leg-dot"));
          leg.appendChild(document.createTextNode(c + " "));
          leg.appendChild(el("span", "tc-leg-cnt", String(perCanton[c])));
          legend.appendChild(leg);
        });
        if (soon.length) {
          var ls = el("span", "tc-leg");
          ls.appendChild(el("span", "tc-leg-dot"));
          ls.appendChild(document.createTextNode("Bientôt (" + soon.join(", ") + ")"));
          legend.appendChild(ls);
        }
      }

      // Infobulles
      function showTip(stageEl, loc, anchor) {
        var t = stageEl.querySelector(".tc-map-tip");
        if (!t) return;
        t.innerHTML = "";
        if (loc === CLUSTER) {
          t.appendChild(el("b", null, "Canton de Fribourg"));
          t.appendChild(el("div", "tc-tip-canton", plural(frLocs.length, "localité")));
          t.appendChild(el("p", "tc-tip-hint", "Cliquez pour voir le zoom détaillé."));
        } else {
          var items = byLoc[loc] || [];
          t.appendChild(el("b", null, loc));
          t.appendChild(el("div", "tc-tip-canton", items.length ? items[0].canton : ""));
          var ul = el("ul");
          items.forEach(function (it) { ul.appendChild(el("li", null, it.name)); });
          t.appendChild(ul);
        }
        var sr = stageEl.getBoundingClientRect();
        var ar = anchor.getBoundingClientRect();
        var y = ar.top - sr.top;
        t.style.left = (ar.left - sr.left + ar.width / 2) + "px";
        t.style.top = y + "px";
        t.classList.toggle("flip", y < (stageEl === insetStage ? sr.height * 0.45 : 110));
        t.classList.add("show");
      }
      function hideTip(stageEl) {
        var t = stageEl.querySelector(".tc-map-tip");
        if (t) t.classList.remove("show");
      }

      function isFr(loc) { return frLocs.indexOf(loc) !== -1; }
      function setPin(loc, cls, on) { if (pins[loc]) pins[loc].btn.classList.toggle(cls, !!on); }
      function highlight(loc, on) {
        if (isFr(loc)) setPin(CLUSTER, "hi", on);
        setPin(loc, "hi", on);
      }

      function focusCards(locs, label) {
        var cards = [];
        entries.forEach(function (p) { if (locs.indexOf(p.loc) !== -1 && !p.card.hidden) cards.push(p.card); });
        if (!cards.length) return;
        try { cards[0].scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth", block: "center" }); } catch (err) {}
        cards.forEach(function (c) {
          c.classList.add("flash");
          setTimeout(function () { c.classList.remove("flash"); }, 1800);
        });
        if (!cards[0].hasAttribute("tabindex")) cards[0].setAttribute("tabindex", "-1");
        try { cards[0].focus({ preventScroll: true }); } catch (err) {}
        live.textContent = plural(cards.length, "commerce") + " " + label + " mis en évidence.";
      }

      Object.keys(pins).forEach(function (loc) {
        var pin = pins[loc];
        pin.btn.addEventListener("mouseenter", function () { showTip(pin.stage, loc, pin.btn); });
        pin.btn.addEventListener("focus", function () { showTip(pin.stage, loc, pin.btn); });
        pin.btn.addEventListener("mouseleave", function () { hideTip(pin.stage); });
        pin.btn.addEventListener("blur", function () { hideTip(pin.stage); });
        pin.btn.addEventListener("click", function () {
          if (loc === CLUSTER) {
            var inset = document.getElementById("tc-pos-inset");
            if (inset) {
              inset.classList.remove("flash");
              void inset.offsetWidth;
              inset.classList.add("flash");
            }
            focusCards(frLocs, "fribourgeois");
          } else {
            focusCards([loc], "à " + loc);
          }
        });
      });
      band.addEventListener("keydown", function (e) {
        if (e.key !== "Escape") return;
        hideTip(stage);
        if (insetStage) hideTip(insetStage);
      });

      function cardLoc(e) {
        var card = e.target.closest && e.target.closest(".tc-pos-card");
        return card ? card.getAttribute("data-loc") : null;
      }
      list.addEventListener("mouseover", function (e) { var l = cardLoc(e); if (l) highlight(l, true); });
      list.addEventListener("mouseout", function (e) { var l = cardLoc(e); if (l) highlight(l, false); });
      list.addEventListener("focusin", function (e) { var l = cardLoc(e); if (l) highlight(l, true); });
      list.addEventListener("focusout", function (e) { var l = cardLoc(e); if (l) highlight(l, false); });

      band.classList.add("tc-map-ready");

      return {
        sync: function (visibleLocs, canton) {
          Object.keys(pins).forEach(function (loc) {
            var visible = loc === CLUSTER
              ? frLocs.some(function (l) { return visibleLocs[l]; })
              : !!visibleLocs[loc];
            setPin(loc, "dim", !visible);
          });
          [svg, insetSvg].forEach(function (s) {
            if (!s) return;
            s.querySelectorAll(".tc-canton.lit").forEach(function (p) { p.classList.remove("lit"); });
            var id = CANTON_ID[canton];
            var p = id && s.querySelector('[data-canton-id="' + id + '"]');
            if (p) p.classList.add("lit");
          });
        }
      };
    }

    render();
  }
})();
