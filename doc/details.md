### Introduction

Which of the following two English sentences is more likely?

```
the dog saw the man with the telescope
```

or:

```
telescope man dog the with a saw
```

It seems obvious that the first sentence is more likely, as the second sentence is grossly grammatically incorrect. However, how about this third sentence:

```
the man saw the dog with the telescope
```

This raises the stakes considerably. Not only is the third sentence perfectly valid and perhaps *more* plausible than the first, but in fact it makes one aware of just how ambiguous the sentences actually are. In the first sentence, is the dog seeing a man with a telescope, or is the dog using a telescope to see a man?

In a very real sense the **ambiguity** of natural languages, like English, are unresolvable if we "just" stare at the text. We need some background, some **context** if you will, that tells us that we live in a world where dogs are not likely to be using telescopes to see men.

I will now attempt to summarise the methods I've used to bring understanding to natural languages. My summary below will be quite cursory so for more details please see [my online course notes](http://files.asimihsan.com/courses/nlp-coursera-2013/notes/nlp.html) on the Natural Language Processing course on Coursera, in particular the material for weeks 1 and 2.

### Language models

The most direct way to get our context is to examine a set of real sentences in a language we're interested in and then make a proverbial map of them. Just like maps do not record every little minute detail about the terrain, we want our models to somehow capture the "essence" or "je ne sais quoi" of the language.

However, our models will be very different to maps in one crucial respect. A map can tell you "if you see a tree there, and a hill here, then you're probably here", i.e. it is a **discriminative** model. We couldn't possibly use a map to create an entirely new world because the map *hasn't captured anything* that would let us do that. We want our language models to be [**generative**](http://stackoverflow.com/questions/879432/what-is-the-difference-between-a-generative-and-discriminative-algorithm), and let us create new sentences that "sort of" look like the underlying language.

### N-Gram Language Models

In an ideal world we would have hundreds of billions of sentences, each completely different from one another. In the real world often we do not have much data; in this case I had access to around 5,200 biographies for either judges or mentors who participated in a Startup Weekend somewhere in the world over the past year. Of those around 2,000 were either not in English or not interesting, for example too short or just bullet points of words. This leaves us with a measley 3,200
biographies!

How can we make a model of something as complicated as English if we don't have enough data? One way is to assume that a sentence is a sequence of words, and the likelihood of a sentence depends on the likelihood of smaller *chunks* within the sentence. For example, in a bigram (or 2-gram) model, with the sentence:

```
The dog ate grapes.
```

We could say that the probability of the sentence in the English language is:

$$
\begin{align}
    &\begin{aligned}
        & p(\textrm{The, dog, ate, grapes}) \\
      = & p(\textrm{START, The}) \times p(\textrm{The, dog}) \\ 
        \times & p(\textrm{dog, ate}) \times p(\textrm{ate, grapes}) \\
        \times & p(\textrm{grapes, STOP})
    \end{aligned}
\end{align}
$$

where START and STOP are special convenience symbols that indicate the start and end of a sentence. Notice how we're now more likely to have much more data, for example the number of sentences that start with "the", however we've made a massive assumption about how sentences "work" in English.

Let's suppose this model is "correct". What are the individual probabilities. For example, what's the probability that a sentence begins with "the"? The models used above are "maximum likelihood" estimates, meaning that:

$$
p(\textrm{START, the}) = \frac{\textrm{Count(START, the)}}{\textrm{Count(START)}}
$$

This is very easy to pull off, and is how the "Bigram Maximum Likelihood" and "Trigram Maximum Likelihood" generator models above work.

### Sparsity

There is an added catch with the trigram case. Consider a data set with the following sentences:

```
the dog chased the cat
the cat chased the dog
the man read a paper
```

Under a trigram maximum-likelihood language model, what is the probability of the following sentence?

```
the man chased the cat
```

One part of the probabilities must be the phrase "man chased the", i.e.:

$$
\begin{align}
    &\begin{aligned}
        p(\textrm{man chased the}) = & \frac{\textrm{Count(man chased the)}}{\textrm{Count(man chased)}} \\
      = & \frac{0}{0} 
    \end{aligned}
\end{align}
$$

Hence there is the possibility of undefined results for some probabilities. This is tedious! Perhaps with much more data we'd just happen to come across this "the man" somewhere, but this isn't a sure-fire solution.

In fact the resolution brings a lot of understanding to the problem. Simply because "man chased that" or "man chased" have never occurred before doesn't mean that *they're impossible*. How do we let our model figuratively shrug and say "well you know I *should* be putting zero here...but I'll give you a pass"?

One of the simplest ways is to say that if a given word is "rare", e.g. has been seen less than 5 times, we "change" it to "__RARE__" or some other special symbol. More advanced methods assign such words to specific rare word classes like "__FOUR_DIGITS__" or "__ALL_CAPITALS__". Please see [Dealing with Low-Frequency Words: An Example](http://files.asimihsan.com/courses/nlp-coursera-2013/notes/nlp.html#dealing-with-low-frequency-words-an-example) in my notes for more details.

In this case I've assigned words that occur less than or equal to 2 times to a __RARE__ token when both training the models and generating new sentences.

### Hidden Markov Models

TODO; please read my class notes for more information. I implemented a Hidden Markov Model such that **part-of-speech** (POS) tags are "transmitted" according to a trigram mode, and each POS tag uses a bigram count to "emit" a word. You'll note that the output of the "Trigram Hidden Markov Model" seems much more creative but a little worse than the "Trigram Maximum Likelihood" model.

### Future work

-   Implement linear interpolation and Katz backoff language models with cross-validation. I'd expect these to be quite superior, so this is the obvious next step.
-   Currently the Hidden Markov Model (HMM) uses trigram transmissions for the POS tags and bigram emissions for a word per tag. I think this model would be considerably improved if one used trigram emissions, such that a word is emitted depending on the previous two tags.
-   I've calculated the perplexities of these models; rougly it's 520 for the unigram model, 6 for the bigram model, 5 for the trigram. The bigram and trigram numbers are far too low so I've made a mistake, and it's worth going back and fixing this.
-   Visualisations for the data?
