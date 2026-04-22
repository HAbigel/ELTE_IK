module KotSzorgalmival where

import Data.Either
import Data.Maybe
import Text.Read -- 2. feladat

-- http://lambda.inf.elte.hu/ShuntingYard.html

basicInstances = 0 -- Mágikus tesztelőnek kell ez, NE TÖRÖLD!

type OperatorTable a = [(Char, (a -> a -> a, Int, Dir))]

tAdd, tMinus, tMul, tDiv, tPow :: (Floating a) => Tok a
tAdd = TokBinOp (+) '+' 6 InfixL
tMinus = TokBinOp (-) '-' 6 InfixL
tMul = TokBinOp (*) '*' 7 InfixL
tDiv = TokBinOp (/) '/' 7 InfixL
tPow = TokBinOp (**) '^' 8 InfixR

operatorTable :: (Floating a) => OperatorTable a
operatorTable =
    [ ('+', ((+), 6, InfixL))
    , ('-', ((-), 6, InfixL))
    , ('*', ((*), 7, InfixL))
    , ('/', ((/), 7, InfixL))
    , ('^', ((**), 8, InfixR))
    ]


getOp :: (Floating a) => Char -> Maybe (Tok a)
getOp = operatorFromChar operatorTable


parse :: String -> Maybe [Tok Double]
parse = parseTokens operatorTable


parseAndEval :: (String -> Maybe [Tok a]) -> ([Tok a] -> ([a], [Tok a])) -> String -> Maybe ([a], [Tok a])
parseAndEval parse eval input = maybe Nothing (Just . eval) (parse input)

syNoEval :: String -> Maybe ([Double], [Tok Double])
syNoEval = parseAndEval parse shuntingYardBasic

syEvalBasic :: String -> Maybe ([Double], [Tok Double])
syEvalBasic = parseAndEval parse (\t -> shuntingYardBasic $ BrckOpen : (t ++ [BrckClose]))


syEvalPrecedence :: String -> Maybe ([Double], [Tok Double])
syEvalPrecedence = parseAndEval parse (\t -> shuntingYardPrecedence $ BrckOpen : (t ++ [BrckClose]))

-- eqError-t vedd ki a kommentből, ha megcsináltad az 1 pontos "Hibatípus definiálása" feladatot
eqError = 0 -- Mágikus tesztelőnek szüksége van rá, NE TÖRÖLD!


-- Ezt akkor vedd ki a kommentblokkból, ha a 3 pontos "A parser és az algoritmus újradefiniálása" feladatot megcsináltad.

parseAndEvalSafe ::
    (String -> ShuntingYardResult [Tok a]) ->
    ([Tok a] -> ShuntingYardResult ([a], [Tok a])) ->
    String -> ShuntingYardResult ([a], [Tok a])
parseAndEvalSafe parse eval input = either Left eval (parse input)

sySafe :: String -> ShuntingYardResult ([Double], [Tok Double])
sySafe = parseAndEvalSafe
  (parseSafe operatorTable)
  (\ts -> shuntingYardSafe (BrckOpen : ts ++ [BrckClose]))



-- Ezt akkor vedd ki a kommentblokkból, ha az 1 pontos "Függvénytábla és a típus kiegészítése" feladatot megcsináltad.
tSin, tCos, tLog, tExp, tSqrt :: Floating a => Tok a
tSin = TokFun sin "sin"
tCos = TokFun cos "cos"
tLog = TokFun log "log"
tExp = TokFun exp "exp"
tSqrt = TokFun sqrt "sqrt"

functionTable :: (RealFrac a, Floating a) => FunctionTable a
functionTable =
    [ ("sin", sin)
    , ("cos", cos)
    , ("log", log)
    , ("exp", exp)
    , ("sqrt", sqrt)
    , ("round", (\x -> fromIntegral (round x :: Integer)))
    ]



-- Ezt akkor vedd ki a kommentblokkból, ha a 2 pontos "Függvények parse-olása és kiértékelése" feladatot megcsináltad.
syFun :: String -> Maybe ([Double], [Tok Double])
syFun = parseAndEval
  (parseWithFunctions operatorTable functionTable)
  (\t -> shuntingYardWithFunctions $ BrckOpen : (t ++ [BrckClose]))



-- Ezt akkor vedd ki a kommentblokkból, ha minden más feladatot megcsináltál ez előtt.
syComplete :: String -> ShuntingYardResult ([Double], [Tok Double])
syComplete = parseAndEvalSafe
  (parseComplete operatorTable functionTable)
  (\ts -> shuntingYardComplete (BrckOpen : ts ++ [BrckClose]))


---------------------------------------------------------------------------------------------------------
-- 1.
data Dir = InfixL | InfixR
   deriving (Show, Eq, Ord)

data Tok a = BrckOpen | BrckClose | TokLit a | TokBinOp (a -> a -> a) Char Int Dir | TokFun (a -> a) String

instance Show a => Show (Tok a) where -- az hogy Show a -t meg lehet csinálni, előfeltétele a Show Tok a -nak
    show BrckOpen = "BrckOpen" 
    show BrckClose = "BrckClose"
    show (TokLit a) = "TokLit " ++ show a
    show (TokBinOp operator opSzimbolum kötErö dir) = "TokBinOp '" ++ [opSzimbolum] ++ "' " ++ show kötErö ++ " " ++ show dir -- mivel op karakter, ezert []
    show (TokFun fv fvNev) =  "TokFun " ++ fvNev

instance Eq a => Eq (Tok a) where
    (==) BrckOpen BrckOpen  = True 
    (==) BrckClose BrckClose = True
    (==) (TokLit a) (TokLit b) = a==b
    (==) (TokBinOp operator1 opSzimbolum1 kötErö1 dir1) (TokBinOp operator2 opSzimbolum2 kötErö2 dir2) = opSzimbolum1==opSzimbolum2 && kötErö1==kötErö2 && dir1==dir2
    (==) (TokFun fv1 fvNev1) (TokFun fv2 fvNev2) = fvNev1 == fvNev2
    (==) _ _ = False

-- Operátorrá alakítás - KÖTELEZŐ

operatorFromChar :: OperatorTable a -> Char -> Maybe (Tok a)
operatorFromChar [] _ = Nothing
operatorFromChar (( cop, (op, szam, dir)):xs) c
    | c==cop = Just (TokBinOp op cop szam dir)
    | otherwise = operatorFromChar xs c

-- String-ek tokenizálása - KÖTELEZŐ
isZarojel :: Char -> Bool
isZarojel '(' = True
isZarojel ')' = True
isZarojel _ = False

mindZarojel :: String -> Bool
mindZarojel szo = all isZarojel szo

zarojelFelbontas :: String -> [String]
zarojelFelbontas szo
    | mindZarojel szo = map (\c -> [c]) szo
    | otherwise = [szo]
   
wordChecker :: (Read a) => OperatorTable a -> String -> Maybe (Tok a) -- forall a. 
wordChecker tabla "(" = Just BrckOpen
wordChecker tabla ")" = Just BrckClose
wordChecker tabla [x]
    | isJust (operatorFromChar tabla x) = operatorFromChar tabla x
    | otherwise = TokLit <$> readMaybe [x] -- a <$> nem a Just x -re, hanem a Juston belüli dologra, tehát csak az x-re alkalmazza a fv-t ami előtte van, lényegében infix fmap -- mint az előző verziómban az unJust
wordChecker tabla szo = TokLit <$> readMaybe szo

-- parseTokens :: (Eq a, Read a) => OperatorTable a -> String -> Maybe [Tok a] -- Talán működik
parseTokens :: Read a => OperatorTable a -> String -> Maybe [Tok a] -- Talán működik
parseTokens _ "" = Just []
parseTokens tabla szoveg = mapM (wordChecker tabla) szavak
    where 
        szavak = concat(map zarojelFelbontas (words szoveg))

-- Alap Shunting Yard algoritmus - kötési erősség és irányok figyelmen kívül hagyása - KÖTELEZŐ

isLit :: (Tok a) -> Bool
isLit (TokLit _) = True
isLit _ = False

unTokLit :: (Tok a) -> a
unTokLit (TokLit x) = x

isBinOp :: (Tok a) -> Bool
isBinOp (TokBinOp _ _ _ _) = True
isBinOp _ = False

takeOp :: Tok a -> (a -> a -> a)
takeOp (TokBinOp op _ _ _) = op

isBO :: (Tok a) -> Bool
isBO BrckOpen = True
isBO _ = False

isBC :: (Tok a) -> Bool
isBC BrckClose = True
isBC _ = False

kiertekel :: [a] -> (a -> a -> a) -> a
kiertekel [x1,x2] op = (op x2 x1)

kiertekelActual :: ([a], [Tok a]) -> (Tok a) -> ([a], [Tok a])
kiertekelActual ([],[]) x
    | isLit x = (((unTokLit x):[]),[])
    | isBinOp x = ([],(x:[]))
    | isBO x = ([],(x:[]))
kiertekelActual (xs,ys) x
    | isLit x = (((unTokLit x):xs),ys)
    | isBinOp x = (xs,(x:ys))
    | isBO x = (xs,(x:ys))
    | ((isBC x) && (isBO (head ys))) = (xs, tail ys)
    | ((isBC x) && (isBO (head (tail ys)))) = ( ((kiertekel (take 2 xs) (takeOp (head ys))) : (drop 2 xs)), (drop 2 ys)) -- ha a kövi BrckOpen azt is leveszi, ne maradjon ott
    | otherwise = kiertekelActual (((kiertekel (take 2 xs) (takeOp (head ys))) : (drop 2 xs)), tail ys) BrckClose  -- ha még nem BrckOpen a kövi, akk ujra meghivjuk a kiertekelActualt

shuntingYardBasic :: [Tok a] -> ([a], [Tok a])
shuntingYardBasic [] = ([],[])
shuntingYardBasic (xs) = (lil, opl)
    where
        (lil, opl) = (foldl (kiertekelActual) ([],[]) xs)
 
-- Az algoritmus javítása - kötési erősségek és irányok figyelembevétele - KÖTELEZŐ
getInfix :: (Tok a) -> Int
getInfix (TokBinOp op opsz koter dir) = koter
getInfix (TokFun fv nev) = maxBound :: Int -- ???
getInfix _ = 0

isDirL :: (Tok a) -> Bool
isDirL (TokBinOp op opsz koter dir) = dir == InfixL

kiertekelForReal :: ([a], [Tok a]) -> (Tok a) -> ([a], [Tok a])
kiertekelForReal ([],[]) x
    | isLit x = (((unTokLit x):[]),[])
    | isBinOp x = ([],(x:[]))
    | isBO x = ([],(x:[]))
    | otherwise = ([],[])
kiertekelForReal (xs,[]) x
    | isLit x = (((unTokLit x):xs),[])
    | isBinOp x = (xs,(x:[]))
    | isBO x = (xs,(x:[]))
    | otherwise = (xs,[])
kiertekelForReal (xs,y:ys) x
    | isLit x = (((unTokLit x):xs),y:ys)
    | isBinOp x = (bop (xs,y:ys) x)
    | isBO x = (xs,(x:y:ys))
    | ((isBC x) && (isBO y)) = (xs, ys)
    | ((isBC x) && (isBO (head ys))) = ((((kiertekel (take 2 xs) (takeOp y))) : (drop 2 xs)), (drop 1 ys))
    | otherwise = kiertekelForReal (((kiertekel (take 2 xs) (takeOp y)) : (drop 2 xs)), ys) BrckClose

bop :: ([a], [Tok a]) -> (Tok a) -> ([a], [Tok a])
bop (xs,[]) u = (xs,[u])
bop (xs,(BrckOpen:ys)) u = (xs,(u:BrckOpen:ys))
bop ((x1:x2:xs),(y:ys)) u
    | isDirL u && (getInfix u <= getInfix y) = kiertekelForReal (((kiertekel [x1,x2] (takeOp y)):xs),(ys)) u
    | (not (isDirL u)) && (getInfix u < getInfix y) = kiertekelForReal (((kiertekel [x1,x2] (takeOp y)):xs),(ys)) u
    | otherwise = ((x1:x2:xs),(u:y:ys))

shuntingYardPrecedence :: [Tok a] -> ([a], [Tok a])
shuntingYardPrecedence [] = ([],[])
shuntingYardPrecedence (xs) = (lil, opl)
    where
        (lil, opl) = (foldl (kiertekelForReal) ([],[]) xs)
        
-- SZORGALMIK
--------------------------------------------------------------------------------------------------
-- (1 + 3 pont) Bemenetvalidálás
-- KÉSZ -- (1 pont) Hibatípus definiálása
data ShuntingYardError = OperatorOrClosingParenExpected | LiteralOrOpeningParenExpected | NoClosingParen | NoOpeningParen | ParseError
    deriving (Show, Eq)
    
type ShuntingYardResult = Either ShuntingYardError

-- (3 pont) A parser és az algoritmus újradefiniálása

-- parse
unJust :: Maybe [Tok a] -> [Tok a]
unJust (Just []) = []
unJust (Just [x]) = [x]
unJust (Just xs) = xs

parseSafe :: Read a => OperatorTable a -> String -> ShuntingYardResult [Tok a]
parseSafe _ "" = Right []
parseSafe tabla szoveg
    | isNothing (parseTokens tabla szoveg) = Left ParseError
    | otherwise = Right (unJust (parseTokens tabla szoveg))


-- sys ------------------------------------------------------------------


data TokType = BCl | BOp | TLit | TBOp | TFun
    deriving (Show, Eq)

getType :: (Tok a) -> TokType
getType BrckClose = BCl
getType BrckOpen = BOp
getType (TokLit _) = TLit
getType (TokBinOp _ _ _ _) = TBOp
getType (TokFun _ _) = TFun

strongErrors = [[TBOp,BCl],[TBOp,TBOp],[BOp,BCl],[BOp,TBOp],[TLit,TLit],[TLit,BOp],[BCl,BOp],[BCl,TLit]]

checkNoError :: [Tok a] -> Bool
checkNoError [x1,x2]
    | not (elem [getType x1,getType x2] strongErrors) = True
    | otherwise = False
checkNoError (x1:x2:xs) = (not (elem [getType x1,getType x2] strongErrors)) && checkNoError (x2:xs)

errorType :: [Tok a] -> [(ShuntingYardResult ([a], [Tok a]))]
errorType [a,b]
    | elem [getType a,getType b] [[TBOp,BCl],[TBOp,TBOp],[BOp,BCl],[BOp,TBOp]] = [Left LiteralOrOpeningParenExpected]
    | elem [getType a,getType b] [[TLit,TLit],[TLit,BOp],[BCl,BOp],[BCl,TLit]] = [Left OperatorOrClosingParenExpected]
    | otherwise =  [Right ([],[])] -- kulonCsekk [a,b]
errorType xs = ((errorType (take 2 xs)) ++ (errorType (tail xs)))

-- YEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEESSSSS

kulonCsekk :: [Tok a] -> [ShuntingYardResult ([a], [Tok a])]
kulonCsekk [] = [Right ([],[])]
kulonCsekk (xs)
    | not (null (filter isBO opl)) = [Left NoClosingParen]
    | otherwise = [Right (lil, opl)]
    where
        (lil, opl) = (foldl (kiertekelForReal) ([],[]) xs)

-- O YEA
isBad :: (Maybe (Tok a),Maybe (Tok a)) -> Bool -- a sok seged fv azert van meg az elem hasznalata azert van kikerulve mert kul Eq a kene feltetelnek
isBad (Just BrckClose,Nothing) = True
isBad _ = False

zipHosszabbig :: [a] -> [b] -> [(Maybe a, Maybe b)]
zipHosszabbig [] [] = []
zipHosszabbig (x:xs) [] = (Just x, Nothing) : zipHosszabbig xs []
zipHosszabbig [] (y:ys) = (Nothing, Just y) : zipHosszabbig [] ys
zipHosszabbig (x:xs) (y:ys) = (Just x, Just y) : zipHosszabbig xs ys

shuntingYardSafe :: [Tok a] -> ShuntingYardResult ([a], [Tok a])
shuntingYardSafe [] = Right ([],[])
shuntingYardSafe (xs)
    | not (checkNoError (xs)) = head (filter isLeft (errorType xs))
    | isLeft (head (kulonCsekk xs)) = (head (kulonCsekk xs))
    | not (null (filter isBad csekkNumBrck)) = Left NoOpeningParen -- length-es helyett... idk miert nem mukodik, a bal oldalra kezi teszttel Truet ad vissza -- rajottem isBad-ben rossz volt a eltetel
    -- | length (filter isBC xs) > length (filter isBO xs) = Left NoOpeningParen -- length
    | otherwise = Right (lil, opl)
    where
        (lil, opl) = (foldl (kiertekelForReal) ([],[]) xs)
        osszBC = (filter isBC xs)
        osszBO = (filter isBO xs)
        csekkNumBrck = zipHosszabbig osszBC osszBO


--------------------------------------------------------------------------------------------------
-- (1 + 2 + 1 pont) Az algoritmus kiegészítése függvényhívásokkal
-- KÉSZ -- (1 pont) Függvénytábla és a típus kiegészítése
type FunctionTable a = [(String, (a -> a))]

-- KÉSZ -- (2) Függvények parse-olása és kiértékelése
-- parse
funFromKif :: FunctionTable a -> String -> Maybe (Tok a)
funFromKif [] _ = Nothing
funFromKif ((nev,fv):xs) kif
    | kif == nev = Just (TokFun fv nev)
    | otherwise = funFromKif xs kif
    
wordCheckerFunc :: (Read a) => OperatorTable a -> FunctionTable a -> String -> Maybe (Tok a) -- forall a. 
wordCheckerFunc tabla fvtabla "(" = Just BrckOpen
wordCheckerFunc tabla fvtabla ")" = Just BrckClose
wordCheckerFunc tabla fvtabla kif
    | isJust (funFromKif fvtabla kif) = funFromKif fvtabla kif 
wordCheckerFunc tabla fvtabla [x]
    | isJust (operatorFromChar tabla x) = operatorFromChar tabla x
    | otherwise = TokLit <$> readMaybe [x]
wordCheckerFunc tabla fvtabla szo = TokLit <$> readMaybe szo
    
parseWithFunctions :: Read a => OperatorTable a -> FunctionTable a -> String -> Maybe [Tok a] 
parseWithFunctions _ _ "" = Just []
parseWithFunctions tabla fvtabla szoveg = mapM (wordCheckerFunc tabla fvtabla) szavak
    where 
        szavak = concat(map zarojelFelbontas (words szoveg))
----------------------------------------------------------------------------------
-- kiertekel
shuntingYardWithFunctions :: [Tok a] -> ([a], [Tok a]) 
shuntingYardWithFunctions [] = ([],[])
shuntingYardWithFunctions (xs) = (lil, opl)
    where
        (lil, opl) = (foldl (kiertekelFunc) ([],[]) xs)

isFv :: (Tok a) -> Bool
isFv (TokFun _ _) = True
isFv _ = False

takeFv :: (Tok a) -> (a -> a)
takeFv (TokFun fv nev) = fv

kiertekelFv :: a -> (a->a) -> a
kiertekelFv x f = f x

kiertekelFunc :: ([a], [Tok a]) -> (Tok a) -> ([a], [Tok a])
kiertekelFunc ([],[]) x
    | isFv x = ([],(x:[]))
    | isLit x = (((unTokLit x):[]),[])
    | isBinOp x = ([],(x:[]))
    | isBO x = ([],(x:[]))
    | otherwise = ([],[])
kiertekelFunc (xs,[]) x
    | isFv x = (xs,[x])
    | isLit x = (((unTokLit x):xs),[])
    | isBinOp x = (xs,(x:[]))
    | isBO x = (xs,(x:[]))
    | otherwise = (xs,[])
kiertekelFunc (xs,y:ys) x
    | isFv x = (xs,(x:y:ys))
    | isLit x = (((unTokLit x):xs),y:ys)
    | isBinOp x = (bopF (xs,y:ys) x)
    | isBO x = (xs,(x:y:ys))
    | isBC x = bcErtekel (xs,y:ys) x

bopF :: ([a], [Tok a]) -> (Tok a) -> ([a], [Tok a])
bopF (xs,[]) u = (xs,[u])
bopF (xs,(BrckOpen:ys)) u = (xs,(u:BrckOpen:ys))
bopF ((x:xs),(y:ys)) u 
    | isFv y = kiertekelFunc ((kiertekelFv x (takeFv y)):xs,ys) u
bopF ((x1:x2:xs),(y:ys)) u
    | isFv y = kiertekelFunc ((kiertekelFv x1 (takeFv y):x2:xs),ys) u
    | isDirL u && (getInfix u <= getInfix y) = kiertekelFunc (((kiertekel [x1,x2] (takeOp y)):xs),(ys)) u
    | (not (isDirL u)) && (getInfix u < getInfix y) = kiertekelFunc (((kiertekel [x1,x2] (takeOp y)):xs),(ys)) u
    | otherwise = ((x1:x2:xs),(u:y:ys))
bopF ([],y:ys) u = ([],(u:y:ys))

bcErtekel :: ([a], [Tok a]) -> (Tok a) -> ([a], [Tok a])
bcErtekel (xs,y:ys) x
    | (isBO y) = (xs, ys)
    | (isBO (head ys)) && (isFv y) = kiertekelFunc ((kiertekelFv (head xs) (takeFv y)):(tail xs),ys) BrckClose
    | (isBO (head ys)) && (isBinOp y) = kiertekelFunc (((kiertekel (take 2 xs) (takeOp y)) : (drop 2 xs)), ys) BrckClose
    | (isBO (head ys)) = kiertekelFunc ((((kiertekel (take 2 xs) (takeOp y))) : (drop 2 xs)), (drop 1 ys)) BrckClose
    | null xs && (isFv y) = (xs,(x:y:ys)) -- ITT
    | (isFv y) = kiertekelFunc ((kiertekelFv (head xs) (takeFv y)):(tail xs),ys) BrckClose
    | otherwise =  kiertekelFunc (((kiertekel (take 2 xs) (takeOp y)) : (drop 2 xs)), ys) BrckClose


-- (+1) Comlete
parseComplete :: Read a => OperatorTable a -> FunctionTable a -> String -> ShuntingYardResult [Tok a] 
parseComplete _ _ "" = Right []
parseComplete tabla fvtabla szoveg
    | isNothing (parseWithFunctions tabla fvtabla szoveg) = Left ParseError
    | otherwise = Right (unJust (parseWithFunctions tabla fvtabla szoveg))
    
shuntingYardComplete :: [Tok a] -> ShuntingYardResult ([a], [Tok a])
shuntingYardComplete [] = Right ([],[])
shuntingYardComplete (xs)
    | not (null (filter isFv opl)) = Left LiteralOrOpeningParenExpected
    | not (checkNoError (xs)) = head (filter isLeft (errorType xs))
    | isLeft (head (kulonCsekk xs)) = (head (kulonCsekk xs))
    | not (null (filter isBad csekkNumBrck)) = Left NoOpeningParen
    | otherwise = Right (lil, opl)
    where
        (lil, opl) = (foldl (kiertekelFunc) ([],[]) xs)
        osszBC = (filter isBC xs)
        osszBO = (filter isBO xs)
        csekkNumBrck = zipHosszabbig osszBC osszBO
