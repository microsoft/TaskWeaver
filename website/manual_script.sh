# for local dev
npm run start

# make sure you're in the website directory
npm run build
cd build

git init
git branch -m gh-pages
git add -A
git commit -m "update the docs"
git remote add origin https://github.com/microsoft/TaskWeaver.git
git push -f origin gh-pages