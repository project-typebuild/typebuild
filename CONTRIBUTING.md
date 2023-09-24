Great! You can replace the placeholder URLs in the CONTRIBUTING.md file with your actual repository URL. Here's how it should look:

# Contributing to TypeBuild

First off, thank you for considering contributing to TypeBuild. It's people like you that make TypeBuild such a great tool.

## Where do I go from here?

If you've noticed a bug or have a feature request, make one! It's generally best if you get confirmation of your bug or approval for your feature request this way before starting work.

## Fork & create a branch

If this is something you think you can fix, then fork TypeBuild and create a branch with a descriptive name.

A good branch name would be (where issue #325 is the ticket you're working on):

```bash
git checkout -b 325-add-dynamic-widgets
```

## Implement your fix or feature

At this point, you're ready to make your changes! Feel free to ask for help; everyone is a beginner at first.

## Get the code

The first thing you'll need to do is get our code onto your machine. Firstly you'll need to fork our repository so you have a copy that you have write access to. Then you can clone your repository.

```bash
git clone https://github.com/yourusername/typebuild
```

## Make a Pull Request

At this point, you should switch back to your master branch and make sure it's up to date with the latest TypeBuild master branch:

```bash
git remote add upstream https://github.com/project-typebuild/typebuild
git checkout master
git pull upstream master
```

Then update your feature branch from your local copy of master, and push it!

```bash
git checkout 325-add-dynamic-widgets
git rebase master
git push --set-upstream origin 325-add-dynamic-widgets
```

Finally, go to GitHub and make a Pull Request.

## Keeping your Pull Request updated

If a maintainer asks you to "rebase" your PR, they're saying that a lot of code has changed, and that you need to update your branch so it's easier to merge.

## Code review

A team member will review your pull request and provide feedback. Please be patient, as this can take some time. If changes are requested, you can commit your changes and push them to your branch.

## Merging a PR (maintainers only)

A PR can only be merged into master by a maintainer if:

- It is passing CI.
- It has been approved by at least one maintainer.