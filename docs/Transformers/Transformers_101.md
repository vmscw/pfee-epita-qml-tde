# Transformers 101

### Brève histoire

Initialement l’architecture du Transformers a été introduite en 2017 dans le papier [“Attention is all you need”](https://arxiv.org/abs/1706.03762). Dans ce papier, l’architecture repose sur le **mécanisme d’attention** (que l’on detaillera plus finement plus tard), l’architecture est aussi hautement parallélisable. 

Au début des transformers, ils étaient employés principalement sur du NLP (natural language processing), autrement dit sur du traitement de texte: traduction, résumé.

### Modeles de langage

Comme on vient de le dire, les transformers ont été intialement entrainés sur du texte en plusieurs étapes:

1. Pre-training
    
    Les modeles sont entrainés de manieres **auto-supervisés*** afin d’apprendre des statistiques sur la langue sur laquelle il est entrainé.
    
2. Fine-tuning (Apprentissage par transfert
    
    Ensuite le modele (qui a deja une compréhension globale de la langue) est entrainé cette fois ci de maniere **supervisé.**
    
    Voici 2 types de taches d’entrainement differents:
    
    - Le modele apprend à prédire le prochain mot, connaissant les mots précédent (approche causale)
        
        ![Capture d’écran 2026-05-29 à 10.04.25.png](Transformers%20101/Capture_decran_2026-05-29_a_10.04.25.png)
        
    - Le modele apprend à prédire un mot masqué [MASK] dans une phrase, connaissant tout les autres mots de la phrase (meme ceux qui viennent apres le mot masqué)
        
        ![Capture d’écran 2026-05-29 à 10.05.40.png](Transformers%20101/Capture_decran_2026-05-29_a_10.05.40.png)
        

### Taille = Performance

De maniere générale, augmenter la taille d’un modele augmente sa capacité d’abstraction et augmente ses performances. Il a meme été démontré qu’il existe des plateaux qui représentent des sortes d’étapes cognitives semblable au developpement du cerveau et aux nombre de neurones. 

Problemes:

- Cout d’entrainement augmente exponentiellement
- Cout d’émission (en kg de CO2) d’entrainement et d’inférence explose aussi.

Entrainer un modele Transformers de tres grande taille coute énormement d’argent. 

C’est pourquoi on parle de modele fondation. On n’entraine plus à partir de zero un modele, mais on se sert de modeles “open weight”, pour pouvoir fine-tuner sur une ou plusieurs taches précises.

![Capture d’écran 2026-05-29 à 10.13.33.png](Transformers%20101/Capture_decran_2026-05-29_a_10.13.33.png)

![Capture d’écran 2026-05-29 à 10.13.48.png](Transformers%20101/Capture_decran_2026-05-29_a_10.13.48.png)

## Architecture générale

**Encodeur**: il recoit une entrée (du texte par exemple) et “l’encode” dans une représentation latente optimisée.

**Decodeur**: il recoit 2 choses: 

- la sortie de l’encodeur: représentation latente de l’input
- Ouputs :
    - Si phase d’entrainement: alors il s’agit de la vrai séquence à predire.
    - Si phase d’inference: alors il s’agit des outputs précédents du modeles (auto-regression).

![Capture d’écran 2026-05-29 à 10.16.02.png](Transformers%20101/Capture_decran_2026-05-29_a_10.16.02.png)

![Capture d’écran 2026-05-29 à 10.35.36.png](Transformers%20101/Capture_decran_2026-05-29_a_10.35.36.png)

Simplement à partir de ces 2 blocs on peut deja construire 3 types de modeles:

- Modele uniquement Encoder : utilisé dans des taches qui nécessitent une bonne compréhesion de l’entrée (ex: classification)
- Modele uniquemeent Decoder : purment génératif (Sample de l’espace latent → espace du langage naturel)
- Modele Encoder + Decoder : sequence-to-sequence = traduction, résumé de texte, etc.. C’est lorsque le modele nécessite une entrée et produit une sortie.

## Domaines d’applications des Transformers

Toute entrée qui peut etre divisés en morceau (**Token**), et qui contient un **ordre**, peut etre utilisé dans un modele Tranformers:

- Vision : Transformers Vision (Carré = Token)
- Son : Sequence temporelle = Token
- Série temporelle : idem
- Données tabulaire : feature = Token

# Mécanisme d’attention

## Couche auto-attention (self attention)

L’idée princiaple est simple:

Chaque token d’une séquence regarde tous les autres tokens pour décider lesquels sont importants pour comprendre son contexte.

### Token

Supposons une séquence de Token $x = \{x_1, x_2, \cdots, x_n\}$

Chaque token est encodé dans une version latente appelée embedding, de dimension d: ${x_i} \in \mathbb{R^d}$

On concatene tout les embeddings $x_i$ dans une matrice: $X \in \mathbb{R^{n \times d}}$.

### Matrices Q, K, V:

Le transformer projette X dans 3 espaces differents:

- **Query** (represente ce que le Token **recherche**)
- **Key** (représente ce que le Token **contient**)
- **Value** (représente ce que le Token **transmet**)

Les projections sont :

- $Q = X W_Q$, $Q \in \mathbb{R^{n \times d_k}}$
- $K = X W_K$, $K \in \mathbb{R^{n \times d_k}}$
- $V = X W_V$, $V \in \mathbb{R^{n \times v}}$

Ou les matrices $W_i$ sont apprises. Q et K sont de memes dimension $n \times d_k$.

### Scores d’attentions

Chaque token $i$ compare sa Query avec toutes les Keys

$s_{i, j} = q_i^{T}k_j$ → produit scalaire : élévé = forte similarité “latente”

Sous forme matricielle : $S = \frac{Q.K^T}{\sqrt{d_k}}$, avec $d_k$ la dimension des vecteurs de Q et K.

![Capture d’écran 2026-05-29 à 11.29.42.png](Transformers%20101/Capture_decran_2026-05-29_a_11.29.42.png)

### Scores d’attention → [0, 1]

Pour réduire les valeurs de S dans [0, 1] on applique softmax à S.

$A = \text{softmax}(S) = \text{softmax}(\frac{Q.K^T}{\sqrt{d_k}})$

où les $A_{i, j}$ représente combien le token i doit preter attention au token j.

### Value

Ensuite on calcule simplemnt le produit $Z = AV$.

Chaque sortie est $z_i = \sum_{j=1}^{n}A_{i, j}v_j$.

Le vecetur $z_i$ est une combinaison linéaire (pondérée par l’attention) des autres valeurs des tokens $v_j$.

$$
\text{Attention(Q, K, V)} = \text{softmax}(\frac{Q.K^T}{\sqrt{d_k}}).V
$$

## Multi-head Attention

Ce mécanisme d’attention est bien, mais il reste contraint à finalement l’apprentissage de 3 matrices, qui peut etre encode seulement la syntaxe.

Pour pouvoir encoder egalement les dépendances a long termes, les relations sémantiques etc.. on ajoute plusieurs head, ou chacune, est censé, apprendre une représentation differentes, et ainsi la “somme” completent la description.

Le multi-head attention est finakement assez simple:

- On choisis un nombre de head : h
- On apprend $W^{(h)}_Q, W^{(h)}_K, W^{(h)}_V$ pour chaque head
- On concatene tout les $Z^{(h)} = \text{Attention}(Q_i, K_i, V_i)$
- On apprend une derniere matrice de projection $W_0$ tel que

$\text{MultiHead(Q, K, V)} = \text{Concat}(Z^{(1)}, Z^{(2)}, \cdots, Z^{(h)}).W_0$

![Capture d’écran 2026-05-29 à 11.54.23.png](Transformers%20101/Capture_decran_2026-05-29_a_11.54.23.png)

## Cross-Attention vs Auto/Self Attention

Dans le cross attention, les **requetes** et les **clés** proviennent de **differentes** sources de données.

Par exemple:

- dans les tâches de traduction automatique, les clés proviennent d’un corpus de textes dans une langue et les requêtes d’une autre langue
- dans les tâches de reconnaissance vocale, les requêtes sont des données audio et les clés des données textuelles permettant de transcrire ces données audio.

Dans le self/auto attention, les **requetes** et les **clés** proviennent de la **meme** source de données.

# Bibliographie

https://huggingface.co/learn/llm-course/fr/chapter1/4

https://arxiv.org/abs/1706.03762

https://www.ibm.com/fr-fr/think/topics/transformer-model